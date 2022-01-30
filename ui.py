import bpy

def mk_video_panel(self, context):
    """Video pannels"""
    scn = bpy.context.scene
    settings = scn.mkvideo_prop
    layout = self.layout
    layout.use_property_split = True
  
    col = layout.column()
    col.label(text='Direct Encode:')

    col.prop(settings, 'sound')
    col.prop(settings, 'rendertrigger')
    col.prop(settings, 'open')

    row = col.row(align=True)
    row.prop(settings, 'quality')
    row.operator("render.make_video", text = "Make video", icon = 'RENDER_ANIMATION') #or icon tiny camera : 'CAMERA_DATA'


    col = layout.column()
    col.label(text='Generate Sequencer:')

    split = col.split(align=True, factor=0.60)
    split.operator("mkvideo.gen_montage_scene", text = "Make Montage Scene", icon = 'SEQUENCE')
    split.operator("mkvideo.gen_montage_from_folder", text = "VSE From Folder", icon = 'FOLDER_REDIRECT')

    # col.operator("mkvideo.gen_montage_scene", text = "Make Montage Scene", icon = 'SEQUENCE')
    # col.operator("mkvideo.gen_montage_from_folder", text = "VSE From Folder", icon = 'FOLDER_REDIRECT')

class MKVIDEO_PT_create_video_ui(bpy.types.Panel):
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_parent_id='RENDER_PT_output'
    bl_label = "Create Video"
    # bl_context = "output"


    def draw(self, context):
        mk_video_panel(self, context)

def register():
    bpy.utils.register_class(MKVIDEO_PT_create_video_ui)
    # bpy.types.RENDER_PT_output.append(mk_video_panel) # direct add in output panel

def unregister():
    bpy.utils.unregister_class(MKVIDEO_PT_create_video_ui)
    # bpy.types.RENDER_PT_output.remove(mk_video_panel) # direct add in output panel
