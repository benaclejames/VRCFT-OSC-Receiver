import bpy

class VIEW3D_PT_VRCFT_Credits(bpy.types.Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    bl_category = "VRCFT"
    bl_label = "Credits"

    def draw(self, context):
        from . import preview_collections

        layout = self.layout
        pcoll = preview_collections["main"]

        # Text label
        box = layout.box()
        col = box.column(align=True)
        text_box = col.box()
        text_box.label(text="VRCFT OSC Receiver", icon="MOD_WAVE")
        text_box.label(text="by benaclejames")
        text_box.label(text="Remember to start VRCFaceTracking", icon="INFO")
        col.separator()
        col.separator()
        row = col.row(align=True)
        row.label(text="Halp I'm unemployed")
        col.separator()
        row = col.row(align=True)
        row.scale_y = 1.5
        kofi_icon = pcoll["kofi"]
        row.operator("wm.url_open", text="Buy me a coffee",
                     icon_value=kofi_icon.icon_id).url = "https://ko-fi.com/benaclejames"
        row = col.row(align=True)
        row.scale_y = 1.5
        twitter_icon = pcoll["twitter"]
        row.operator("wm.url_open", text="Follow me on Twitter",
                     icon_value=twitter_icon.icon_id).url = "https://twitter.com/benaclejames"
        row = col.row(align=True)
        row.scale_y = 1.5
        patreon_icon = pcoll["patreon"]
        row.operator("wm.url_open", text="Support me on Patreon",
                     icon_value=patreon_icon.icon_id).url = "https://www.patreon.com/benaclejames"
        row = col.row(align=True)
        row.label(text="Thanks so much for your support!", icon="BLENDER")