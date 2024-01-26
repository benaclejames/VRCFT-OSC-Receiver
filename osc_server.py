import bpy
import queue
import socket
import threading
import select
from . import osc_wrapper

thread = None
recv_sock = None
cancellation_token = False
shape_keys = {}
cached_address_conversions = {}
message_queue = queue.Queue()


def shutdown():
    global thread
    global recv_sock
    global cancellation_token

    cancellation_token = True
    recv_sock.shutdown(socket.SHUT_RDWR)
    if thread is not None:
        thread.join()
        thread = None
    set_remote_all_params_relevant(False)


def process_osc_message(address, osc_data, standard):
    if address not in cached_address_conversions:
        split = address.split("/")
        protocol = split[3]
        if protocol != "v2":
            protocol = "v1"
        name = split[-1]
        if protocol != standard:
            return

        cached_address_conversions[address] = name.lower()
    param_name = cached_address_conversions[address]
    if param_name in shape_keys:
        shape_key = shape_keys[param_name]
        if shape_key is not None:
            shape_key.value = osc_data


def recv_and_process(standard):
    # While our cancellation token is false, keep receiving and processing messages
    while not cancellation_token:
        # Use select to know when we have data to receive
        ready = select.select([recv_sock], [], [], 0.1)
        if ready[0]:
            # Receive the data
            try:
                data, addr = recv_sock.recvfrom(4096)
            except BrokenPipeError:  # If the socket is shut down, we'll get this error
                return
            # Parse the data
            index = 0
            success = False
            while success or index == 0:
                address, osc_data, index, success = osc_wrapper.parse_osc_wrapper(data, index)
                if success:
                    message_queue.put((address, osc_data, standard))


def set_remote_all_params_relevant(new_value):
    send_bytes = osc_wrapper.create_osc_bool("/vrcft/settings/forceRelevant", new_value)
    send_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    send_sock.sendto(send_bytes, ("127.0.0.1", 9001))

def execute_queued_functions():
    while not message_queue.empty():
        (address, osc_data, standard) = message_queue.get()
        process_osc_message(address, osc_data, standard)
    return 0

class VRCFT_OSC_Server(bpy.types.Operator):
    """Start OSC Server"""
    bl_idname = "wm.vrcft_osc_server"
    bl_label = "OSC Server"

    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        global thread
        global recv_sock
        global cancellation_token
        global shape_keys
        global cached_address_conversions

        wm = context.window_manager

        if wm.vrcft_osc_server_active:
            shutdown()
        else:
            cancellation_token = False
            shape_keys = {}
            cached_address_conversions = {}

            # If the mesh has no blend shapes, return an error
            if context.scene.vrcft_target_mesh is None:
                self.report({'ERROR'}, "Mesh not set")
                return {'CANCELLED'}

            if context.scene.vrcft_target_mesh.shape_keys is None:
                self.report({'ERROR'}, "Mesh has no blendshapes")
                return {'CANCELLED'}

            for key in context.scene.vrcft_target_mesh.shape_keys.key_blocks:
                name = key.name.replace(context.scene.vrcft_shapekey_prefix, "").replace('_', '').lower()
                shape_keys[name] = key

            # Get the value of the enum row.prop(scene, "vrcft_shapekey_standard", text="Shapekey Standard")
            prop = context.scene.vrcft_shapekey_standard

            recv_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            recv_sock.bind(("127.0.0.1", context.scene.vrcft_osc_port))
            thread = threading.Thread(target=recv_and_process, args=(prop,))
            thread.start()

            # Now tell vrcft to start sending all osc messages
            set_remote_all_params_relevant(True)
            bpy.app.timers.register(execute_queued_functions)

        wm.vrcft_osc_server_active = not wm.vrcft_osc_server_active
        return {'FINISHED'}
