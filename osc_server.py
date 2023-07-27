import bpy
import socket
import threading
import os
import select
from . import osc_wrapper

thread = None
recv_sock = None
cancellation_token = False
shape_keys = {}
cached_address_conversions = {}


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


def process_osc_message(address, osc_data):
    if address not in cached_address_conversions:
        cached_address_conversions[address] = address.split("/")[-1].lower()
    param_name = cached_address_conversions[address]
    if param_name in shape_keys:
        shape_key = shape_keys[param_name]
        if shape_key is not None:
            shape_key.value = osc_data


def recv_and_process():
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
            address, osc_data, message_index, success = osc_wrapper.parse_osc_wrapper(data)
            # If the parse was successful, process the message
            if success:
                process_osc_message(address, osc_data)


def set_remote_all_params_relevant(new_value):
    send_bytes = osc_wrapper.create_osc_bool("/vrcft/settings/forceRelevant", new_value)
    send_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    send_sock.sendto(send_bytes, ("127.0.0.1", 9001))


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

        wm = context.window_manager

        if wm.vrcft_osc_server_active:
            shutdown()
        else:
            cancellation_token = False
            shape_keys = {}

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

            recv_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            recv_sock.bind(("127.0.0.1", context.scene.vrcft_osc_port))
            thread = threading.Thread(target=recv_and_process)
            thread.start()

            # Now tell vrcft to start sending all osc messages
            set_remote_all_params_relevant(True)

        wm.vrcft_osc_server_active = not wm.vrcft_osc_server_active
        return {'FINISHED'}
