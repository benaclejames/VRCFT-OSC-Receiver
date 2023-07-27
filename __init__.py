bl_info = {
    "name": "VRCFT OSC Receiver",
    "author": "benaclejames",
    "version": (1, 1, 0),
    "blender": (2, 80, 0),
    "location": "3D Viewport > Sidebar > VRCFT OSC",
    "description": "Allows you to receive OSC messages from VRCFT and use them to control blendshapes in Blender.",
    "category": "Animation",
}

import bpy
from bpy.utils import previews
import os

preview_collections = {}


class VIEW3D_PT_VRCFT_Receiver(bpy.types.Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    bl_category = "VRCFT"
    bl_label = "OSC Receiver Config"

    def draw(self, context):
        """define the layout of the panel"""
        layout = self.layout
        scene = context.scene
        wm = context.window_manager

        # Text label
        box = layout.box()
        col = box.column(align=True)
        row = col.row(align=True)
        row.label(text="OSC Server", icon="MOD_WAVE")
        col.separator()
        row = col.row(align=True)
        server_button_text = wm.vrcft_osc_server_active and "Stop OSC Server" or "Start OSC Server"
        if scene.vrcft_target_mesh is None:
            row.enabled = False
            server_button_text = "Mesh not set"
        row.operator("wm.vrcft_osc_server", text=server_button_text)
        row = col.row(align=True)
        row.prop(scene, "vrcft_osc_port", text="Receive Port")
        row = col.row(align=True)
        row.prop(scene, "vrcft_shapekey_standard", text="Shapekey Standard")

        col.separator()
        col.separator()

        row = col.row(align=True)
        row.label(text="Mesh Config", icon="MESH_MONKEY")
        col.separator()
        row = col.row(align=True)
        row.prop(scene, "vrcft_target_mesh", text="Mesh")
        row = col.row(align=True)
        row.prop(scene, "vrcft_shapekey_prefix", text="ShapeKey Prefix")


from .credits import VIEW3D_PT_VRCFT_Credits
from .osc_server import VRCFT_OSC_Server, shutdown

shapekey_standards = bpy.props.EnumProperty(
    items=[
        ("v1", "V1", "V1"),
        ("v2", "V2", "V2"),
    ],
    name="Shapekey Standards",
    description="Which version of VRCFT are you using?",
    default="v2"
)


def register():
    pcoll = bpy.utils.previews.new()

    pcoll.load("patreon", os.path.join(os.path.dirname(__file__), "res", "icons", "patreon.png"), "IMAGE")
    pcoll.load("kofi", os.path.join(os.path.dirname(__file__), "res", "icons", "kofi.png"), "IMAGE")
    pcoll.load("twitter", os.path.join(os.path.dirname(__file__), "res", "icons", "twitter.png"), "IMAGE")
    preview_collections["main"] = pcoll

    bpy.types.WindowManager.vrcft_osc_server_active = bpy.props.BoolProperty(default=False)
    bpy.types.Scene.vrcft_osc_port = bpy.props.IntProperty(default=9000)
    bpy.types.Scene.vrcft_target_mesh = bpy.props.PointerProperty(type=bpy.types.Mesh)
    bpy.types.Scene.vrcft_shapekey_prefix = bpy.props.StringProperty()
    bpy.types.Scene.vrcft_shapekey_standard = shapekey_standards

    bpy.utils.register_class(VRCFT_OSC_Server)
    bpy.utils.register_class(VIEW3D_PT_VRCFT_Receiver)
    bpy.utils.register_class(VIEW3D_PT_VRCFT_Credits)


def unregister():
    shutdown()

    bpy.utils.unregister_class(VRCFT_OSC_Server)
    bpy.utils.unregister_class(VIEW3D_PT_VRCFT_Receiver)
    bpy.utils.unregister_class(VIEW3D_PT_VRCFT_Credits)


if __name__ == "__main__":
    register()
