import bpy

def mk_video_panel(self, context):
    """Video pannels"""
    scn = bpy.context.scene
    settings = scn.mkvideo_prop
    layout = self.layout
    layout.use_property_split = True
    

    col = layout.column()
    col.label(text='Create Video:')
    # split = col.split(factor=.5, align=True)
    # split.prop(settings, 'quality')
    # split.operator("render.make_video", text = "Make video", icon = 'RENDER_ANIMATION') #or icon tiny camera : 'CAMERA_DATA'
    
    row = col.row(align=True)
    row.prop(settings, 'quality')
    row.operator("render.make_video", text = "Make video", icon = 'RENDER_ANIMATION') #or icon tiny camera : 'CAMERA_DATA'
    
    row = col.row(align=False)
    row.prop(settings, 'rendertrigger')
    row.prop(settings, 'open')

    row = col.row(align=False)
    row.operator("mkvideo.gen_montage_scene", text = "Make Montage Scene", icon = 'SEQUENCE')


def register():
    bpy.types.RENDER_PT_output.append(mk_video_panel)

def unregister():
    bpy.types.RENDER_PT_output.remove(mk_video_panel)
