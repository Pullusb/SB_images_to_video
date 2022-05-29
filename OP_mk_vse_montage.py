import bpy
import os
import re
from pathlib import Path
from bpy_extras.io_utils import ImportHelper
from . import fn

def set_video_export_settings(scn):
    prefs = fn.get_prefs()
    im_settings_attr = ['file_format','color_mode','quality']
    ff_attr = ['format','codec','constant_rate_factor','ffmpeg_preset','gopsize','use_max_b_frames','max_b_frames','use_lossless_output','video_bitrate','minrate','maxrate','muxrate','packetsize','buffersize','use_autosplit','audio_codec','audio_channels','audio_bitrate','audio_volume','audio_mixrate']
    
    for attr in im_settings_attr:
        if hasattr(scn.render.image_settings, attr):
            setattr(scn.render.image_settings, attr, getattr(prefs, attr))
    
    for attr in ff_attr:
        if hasattr(scn.render.ffmpeg, attr):
            setattr(scn.render.ffmpeg, attr, getattr(prefs, attr))
    
    # disable Lut
    scn.view_settings.view_transform = 'Standard'
    scn.render.use_sequencer = True

def get_resolution(f):
    img = bpy.data.images.load(f, check_existing=True)
    return img.size

class MKVIDEO_OT_gen_montage_scene(bpy.types.Operator):
    """Create a montage VSE scene with rendered images and settings from current scene"""
    bl_idname = "mkvideo.gen_montage_scene"
    bl_label = "Generate Montage Scene"
    bl_options = {'REGISTER'}

    mode : bpy.props.EnumProperty(
        name='Montage scene already exists',
        default='REPLACE_SCENE',
        description='Choose what to do with existing scene',
        items=(
            ('REPLACE_SCENE', 'Replace scene', 'Delete montage scene and start over'),
            ('REPLACE_CONTENT', 'Replace content', 'Replace the scene VSE content but do not touch scene settings'),
            ),)

    def invoke(self, context, event):
        if context.scene.name.endswith('_montage'):
            self.report({'ERROR'}, f'Your already in a montage scene')
            return {'CANCELLED'}

        fp = context.scene.render.filepath
        if not fp:
            self.report({'ERROR'}, 'No filepath to look image for')
            return {'CANCELLED'}
        self.montage_name = context.scene.name + '_montage'
        if bpy.data.scenes.get(self.montage_name):
            # if a montage scene exists, ask what-to-do
            return context.window_manager.invoke_props_dialog(self)
        
        return self.execute(context)
        # return context.window_manager.invoke_props_dialog(self) # , width=250
    
    def draw(self, context):
        layout = self.layout
        layout.label(text='Montage scene already exists, choose action:')
        layout.prop(self, 'mode')

    @staticmethod
    def apply_settings(src_scn, dest_scn):
        set_video_export_settings(dest_scn)
        dest_scn.render.fps = src_scn.render.fps
        dest_scn.render.resolution_x = src_scn.render.resolution_x
        dest_scn.render.resolution_y = src_scn.render.resolution_y
        dest_scn.render.resolution_percentage = 100
        dest_scn.frame_start = src_scn.frame_start
        dest_scn.frame_end = src_scn.frame_end

    def execute(self, context):
        fp = context.scene.render.filepath
        
        name = None
        outpath = os.path.abspath(bpy.path.abspath(fp))
        outpath = Path(outpath)
        if fp.endswith(('\\', '/')):
            outfolder = outpath
            video_name = outpath.name
        else:
            outfolder = outpath.parent
            name = outpath.name
            video_name = outpath.name.rstrip(('.#_-'))
        
        if not outfolder.exists():
            self.report({'ERROR'}, f'Destination not exists {outfolder}')
            return {'CANCELLED'}

        if not outfolder.is_dir():
            self.report({'ERROR'}, f'Destination not detected as a directory {outfolder}')
            return {'CANCELLED'}
        
        # self.report({'ERROR'}, f'OK: {outfolder}') #Dbg

        files = fn.get_files(outpath)
        if not files:
            errtype = f"No file starting with '{name}'" if name else "No numerated file"
            self.report({'ERROR'}, f'{errtype} in {outfolder}')
            return {'CANCELLED'}

        src_scn = context.scene
        
        montage_scn_name = self.montage_name
        montage_scn = bpy.data.scenes.get(montage_scn_name)
        

        if not montage_scn:
            montage_scn = bpy.data.scenes.new(montage_scn_name)
            self.apply_settings(src_scn, montage_scn)
        
        else:
            if self.mode == 'REPLACE_SCENE':
                # delete and recreate
                bpy.data.scenes.remove(montage_scn)
                montage_scn = bpy.data.scenes.new(montage_scn_name)
                self.apply_settings(src_scn, montage_scn)
            
            elif self.mode == 'REPLACE_CONTENT':
                montage_scn.sequence_editor_clear()
                # here we keep existing scene settings

        start = src_scn.frame_start

        ## alternatively check frame start/end from files
        #frame_start = int(re.search(r'\d{2,6}', files[0].name).group(0))
        #frame_end = int(re.search(r'\d{2,6}', files[-1].name).group(0))

        ## switch to scene (and set VSE workspace)
        bpy.context.window.scene = montage_scn

        video_wk = bpy.data.workspaces.get('Video Editing')
        if video_wk:
            context.window.workspace = video_wk
        else:
            video_wk_path = Path(bpy.utils.resource_path('LOCAL'), 'scripts/startup/bl_app_templates_system/Video_Editing/startup.blend')
            if video_wk_path.exists:
                bpy.ops.workspace.append_activate(idname='Video Editing', filepath=str(video_wk_path))
            else:
                print('Video Editing workspace file not found. No workspace switch')

        ## import images in VSE and set in / out (reuse frame rate from active scene)
        vse = montage_scn.sequence_editor_create()

        ## ~copy~ link over sounds strip that might exists in other scene.
        svse = src_scn.sequence_editor
        if svse:
            for s in svse.sequences_all:
                if s.type != 'SOUND':
                    continue

                ## TODO check if there is a way to directly link a strip (would be awesome)
                ns = vse.sequences.new_sound(name=s.name, filepath=s.sound.filepath, channel=s.channel, frame_start=s.frame_start)
                ns.sound = s.sound # reget the same sound source
                
                for attr in ('frame_final_start','frame_final_end','frame_still_start','frame_still_end','frame_offset_start','frame_offset_end','pitch','pan','show_waveform','speed_factor','volume','mute'):
                    if hasattr(s, attr):
                        setattr(s, attr, getattr(ns, attr))
                ## TODO also no effect strip transfer ...
       
        # if not specified, start will be montage_scn start
        chan = fn.get_next_available_channel(scn=montage_scn, start_from=5)
        strip_name = outfolder.name if not name else name.rstrip('_')
        fn.add_frames_to_scene(montage_scn, fp=fp, strip_name=strip_name, channel=chan, start_frame=start) # pass outpath to give an absolute path


        ## prefill output
        check = [i.name for i in os.scandir(outpath.parent) if i.name.startswith(video_name) and i.is_file()]
        if check: # versionning of the file if already exists
            video_name = video_name + "_" + str(len(check) + 1).zfill(2)
        montage_scn.render.filepath = str(outpath.parent / video_name)

        return {'FINISHED'}


class MKVIDEO_OT_gen_montage_from_folder(bpy.types.Operator, ImportHelper):
    """Create a montage VSE scene from a chosen image sequence or a video file"""
    bl_idname = "mkvideo.gen_montage_from_folder"
    bl_label = "Generate Montage From Folder"
    bl_options = {'REGISTER'}

    # mode : bpy.props.EnumProperty(
    #     name='Montage scene already exists',
    #     default='REPLACE_SCENE',
    #     description='Choose what to do with existing scene',
    #     items=(
    #         ('REPLACE_SCENE', 'Replace scene', 'Delete montage scene and start over'),
    #         ('REPLACE_CONTENT', 'Replace content', 'Replace the scene VSE content but do not touch scene settings'),
    #         ),)

    # Overwrite
    
    # Set FPS manually
    fps : bpy.props.IntProperty(name='Frame Rate', default=24, min=1, description='Set frame rate of new scene')

    # new_scene : bpy.props.BoolProperty(name='Make New Scene', default=True, 
    #     description='Import and modify in the current scene instead of creating a new one')

    overwrite_scn : bpy.props.BoolProperty(name='Overwrite Existing Scene', default=False, 
        description='If scene already exists, overwrite instead of abort (scene name: "folder name" + "_edit")')
    

    # directory = bpy.props.StringProperty(subtype='DIR_PATH')
    
    filepath : bpy.props.StringProperty(
        name="File Path", 
        description="File path used for import", 
        maxlen= 1024)
    
    def execute(self, context):
        # fp = context.scene.render.filepath
        fp = self.filepath

        outpath = Path(fp)
        outfolder = outpath if outpath.is_dir() else outpath.parent

        is_video = fn.is_video(outpath)
        if is_video:
            name = outpath.stem
        else:
            files = fn.get_files(outpath) # list of scandir entry
            if not files:
                errtype = f"No numerated file"
                self.report({'ERROR'}, f'{errtype} in {outfolder}')
                return {'CANCELLED'}
            name = outfolder.name

        cl_name = bpy.path.clean_name(name)
        montage_scn_name = f'{cl_name}_edit'

        # create scene and switch to it
        montage_scn = bpy.data.scenes.get(montage_scn_name)
        

        if not self.overwrite_scn and montage_scn: # Abort
            self.report({'ERROR'}, f'Scene "{montage_scn}" already exists, Abort')
            return {'CANCELLED'}

        if montage_scn: # Delete already existing scene
            bpy.data.scenes.remove(montage_scn)

        montage_scn = bpy.data.scenes.new(montage_scn_name)
        set_video_export_settings(montage_scn)
        
        bpy.context.window.scene = montage_scn
        
        if not is_video:
            montage_scn.render.fps = self.fps

        video_wk = bpy.data.workspaces.get('Video Editing')
        if video_wk:
            context.window.workspace = video_wk
        else:
            video_wk_path = Path(bpy.utils.resource_path('LOCAL'), 'scripts/startup/bl_app_templates_system/Video_Editing/startup.blend')
            if video_wk_path.exists:
                bpy.ops.workspace.append_activate(idname='Video Editing', filepath=str(video_wk_path))
            else:
                print('Video Editing workspace file not found. No workspace switch')

        _vse = montage_scn.sequence_editor_create()

        chan = fn.get_next_available_channel(scn=montage_scn, start_from=5)

        if is_video:
            vstrip = fn.add_video_to_scene(montage_scn, fp=fp, strip_name=cl_name, channel=chan+1, start_frame=1) # chan+1 to load sound below
            # set scene fps to match video
            montage_scn.render.fps = int(vstrip.elements[0].orig_fps)
            montage_scn.render.resolution_x = vstrip.elements[0].orig_width
            montage_scn.render.resolution_y = vstrip.elements[0].orig_height
            vstrip.blend_type = 'ALPHA_OVER'
        else:
            fn.add_frames_to_scene(montage_scn, fp=fp, strip_name=cl_name, channel=chan, start_frame=1)

            # check resolution of first image
            res = get_resolution(files[0].path)
            if res:
                montage_scn.render.resolution_x = res[0]
                montage_scn.render.resolution_y = res[1]
            montage_scn.render.resolution_percentage = 100
            montage_scn.frame_start = 1
            montage_scn.frame_end = len(files) - 1

        ## prefill output
        video_name = cl_name # directly use end folder as video name
        check = [i.name for i in os.scandir(outfolder.parent) if i.name.startswith(video_name) and i.is_file()]
        if check: # versionning of the file if already exists
            video_name = video_name + "_" + str(len(check) + 1).zfill(2)
        montage_scn.render.filepath = str(outfolder.parent / video_name)

        return {'FINISHED'}



classes = (
MKVIDEO_OT_gen_montage_scene,
MKVIDEO_OT_gen_montage_from_folder,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
