'''
Created by Samuel Bernou
2015
samuel.bernou@outlook.com

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

bl_info = {
    "name": "imgs2video",
    "description": "Generate a video from image sequences",
    "author": "Samuel Bernou ",
    "version": (1, 5, 0),
    "blender": (2, 80, 0),
    "location": "Properties > Render > Output",
    "warning": "",
    "doc_url": "",
    "category": "System" }

import bpy, os, re
from bpy.app.handlers import persistent
from pathlib import Path
from time import time
import subprocess
import shlex

from bpy.props import (StringProperty,
                        IntProperty,
                        BoolProperty,
                        EnumProperty,
                        FloatProperty)

Qfix = True #bool add suffix to name with quality
subpross = True
################## functions and operators

@persistent
def post_mkvideo(scene):
    #if auto-launch is ticked
    if scene.MVrendertrigger:
        #launch mk video
        bpy.ops.render.make_video()


def get_prefs():
    prefs = bpy.context.preferences
    return prefs.addons[__package__].preferences

def IsImage(head, i):
    if not os.path.isfile(os.path.join(head,i)):
        return False
    imgsTypeList = ["png", "jpg", "bmp", "tiff", "jpeg", "exr", "tga"]
    for ext in imgsTypeList:
        if i.lower().endswith(ext):
            return True
    return False

def get_vse_override():
    for window in bpy.context.window_manager.windows:
        screen = window.screen
        for area in screen.areas:
            if area.type == 'SEQUENCE_EDITOR':
                #for region in area.regions:
                #    if region.type == 'WINDOW':
                return {'window': window, 'screen': screen, 'area': area}

class MKVIDEO_OT_check_ffmpeg(bpy.types.Operator):
    """check if ffmpeg is in path"""
    bl_idname = "mkvideo.check_ffmpeg"
    bl_label = "Check ffmpeg in system path"
    bl_options = {'REGISTER', 'INTERNAL'}
    
    def invoke(self, context, event):
        import  shutil
        self.ok = shutil.which('ffmpeg')
        return context.window_manager.invoke_props_dialog(self, width=250)
    
    def draw(self, context):
        layout = self.layout
        if self.ok:
            layout.label(text='Ok ! ffmpeg is in system PATH', icon='INFO')
        else:
            layout.label(text='ffmeg is not in system PATH', icon='CANCEL')

    def execute(self, context):
        return {'FINISHED'}


def set_video_export_settings(scn):
    prefs = get_prefs()
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


def get_next_available_channel(scn=None, start_from=1):
    '''return available channel starting from chosen index'''
    scn = scn or bpy.context.scene
    vse = scn.sequence_editor
    used_channel = tuple([s.channel for s in vse.sequences_all])
    for i in range(start_from, 256):
        if not i in used_channel:
            return i

def get_files(outpath):
    '''return files as list of scandir object'''

    outpath = Path(outpath)
    if outpath.exists() and outpath.is_dir():
        outfolder = outpath
        name = None
    elif outpath.parent.exists():
        outfolder = outpath.parent
        name = outpath.name
        print()
    else:
        return

    redigit = re.compile(r'\d{4}')
    if name and '#' in name:
        hash_res =re.search(r'(#+)(?!.*#)', 'name')
        hash_num = len(hash_res.group(1))
        redigit = re.compile(f'\d{{{hash_num}}}')

    files = os.scandir(outfolder)
    files = [f for f in files if f.is_file() and redigit.search(f.name)] # filter only filename with sequence number
    files.sort(key=lambda x: x.name)

    if name:
        files = [f for f in files if f.name.startswith(name)]
    # else:
    #     files = [f for f in files if os.path.splitext(f.name)[0].isdigit()] # stem should be only digit
    return files

def add_frames_to_scene(scn, fp, strip_name=None, channel=None, start_frame=None):
    '''Set sequence on scn from fp'''
    vse = scn.sequence_editor
    if start_frame is None:
        start_frame = scn.frame_start
    
    if not channel:
        channel = get_next_available_channel(scn=scn, start_from=1)

    outpath = os.path.abspath(bpy.path.abspath(fp)) # convert to abspath
    
    if not strip_name:
        strip_name = outpath.name.rstrip('_') if not outpath.exists() else outpath.parent.name
    
    files = get_files(outpath)
    if not files:
        return
    seq = vse.sequences.new_image(
        name=strip_name, filepath=files[0].path, channel=5, frame_start=start_frame, fit_method='ORIGINAL')
    ## fit method in  ('FIT', 'FILL', 'STRETCH', 'ORIGINAL') default : 'ORIGINAL'
    for img in files[1:]:
       seq.elements.append(img.name)
    
    return seq

class MKVIDEO_OT_gen_montage_scene(bpy.types.Operator):
    """Create a montage VSE scene with rendered images"""
    bl_idname = "mkvideo.gen_montage_scene"
    bl_label = "Generate Montage Scene"
    bl_options = {'REGISTER'}

    mode : EnumProperty(
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
        
        name = None
        outpath = os.path.abspath(bpy.path.abspath(fp))
        outpath = Path(outpath)
        if fp.endswith(('\\', '/')):
            outfolder = outpath
        else:
            outfolder = outpath.parent
            name = outpath.name
        
        if not outfolder.exists():
            self.report({'ERROR'}, f'Destination not exists {outfolder}')
            return {'CANCELLED'}

        if not outfolder.is_dir():
            self.report({'ERROR'}, f'Destination not detected as a directory {outfolder}')
            return {'CANCELLED'}
        
        # self.report({'ERROR'}, f'OK: {outfolder}') #Dbg

        files=get_files(outpath)
        if not files:
            errtype = f"No file starting with '{name}'" if name else "No numerated file"
            self.report({'ERROR'}, f'{errtype} in {outfolder}')
            return {'CANCELLED'}

        src_scn = context.scene
        montage_scn_name = context.scene.name + '_montage'

        montage_scn = bpy.data.scenes.get(montage_scn_name)
        if not montage_scn:
            montage_scn = bpy.data.scenes.new(montage_scn_name)
        else:
            if self.mode == 'REPLACE_SCENE':
                # delete and recreate
                bpy.data.scenes.remove(montage_scn)
                montage_scn = bpy.data.scenes.new(montage_scn_name)
            elif self.mode == 'REPLACE_CONTENT':
                montage_scn.sequence_editor_clear()
                
                pass
        
        set_video_export_settings(montage_scn)
        montage_scn.render.fps = src_scn.render.fps
        montage_scn.render.resolution_x = src_scn.render.resolution_x
        montage_scn.render.resolution_y = src_scn.render.resolution_y
        montage_scn.render.resolution_percentage = 100
        montage_scn.frame_start = src_scn.frame_start
        montage_scn.frame_end = src_scn.frame_end
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
                ## no effect strip...
       
        # if not specified, start will be passed scene start
        chan = get_next_available_channel(scn=montage_scn, start_from=5)
        strip_name = outfolder.name if not name else name.rstrip('_')
        seq = add_frames_to_scene(montage_scn, fp=fp, strip_name=strip_name, channel=chan, start_frame=start) # pass outpath to give an absolute path
        
        return self.execute(context)
        # return context.window_manager.invoke_props_dialog(self) # , width=250
    
    # def draw(self, context):
    #     layout = self.layout
    #     if self.ok:
    #         layout.label(text='Ok ! ffmpeg is in system PATH', icon='INFO')
    #     else:
    #         layout.label(text='ffmeg is not in system PATH', icon='CANCEL')

    def execute(self, context):
        return {'FINISHED'}

class imgs2videoPreferences(bpy.types.AddonPreferences):
    bl_idname = __name__

    path_to_ffmpeg : StringProperty(
        name="Path to ffmpeg binary",
        subtype='FILE_PATH',)

    ## Stored preferences for video scene settings
    
    file_format : EnumProperty(
        name='File Format',
        items=(
            ('AVI_JPEG', 'AVI JPEG', 'Output video in AVI JPEG format'),
            ('AVI_RAW', 'AVI Raw', 'Output video in AVI Raw format'),
            ('FFMPEG', 'FFmpeg Video', 'The most versatile way to output video files'),
        ),
        default='FFMPEG',
        description='File format to save the rendered images as',
    )

    color_mode : EnumProperty(
        name='Color Mode',
        default='RGB',
        description='Choose BW for saving grayscale, RGB for saving red, green and blue channels, and RGBA for saving red, green, blue and alpha channels',
        items=(
            ('BW', 'BW', 'grayscale'),
            ('RGB', 'RGB', 'RGB (color) data'),
            ),)

    quality : IntProperty(name="Quality",
        description="Quality for format with loss compression",
        default=90, min=0, max=100, step=1, subtype='PERCENTAGE', options={'HIDDEN'})

    format : EnumProperty(
        name='Container',
        default='MKV',
        description='Output file container',
        items=(
            ('MPEG1', 'MPEG-1', ''),
            ('MPEG2', 'MPEG-2', ''),
            ('MPEG4', 'MPEG-4', ''),
            ('AVI', 'AVI', ''),
            ('QUICKTIME', 'Quicktime', ''),
            ('DV', 'DV', ''),
            ('OGG', 'Ogg', ''),
            ('MKV', 'Matroska', ''),
            ('FLASH', 'Flash', ''),
            ('WEBM', 'WebM', ''),
            ),)

    codec : EnumProperty(
        name='Video Codec',
        default='H264',
        description='FFmpeg codec to use for video output',
        items=(
            ('NONE', 'No Video', 'Disables video output, for audio-only renders'),
            ('DNXHD', 'DNxHD', ''),
            ('DV', 'DV', ''),
            ('FFV1', 'FFmpeg video codec #1', ''),
            ('FLASH', 'Flash Video', ''),
            ('H264', 'H.264', ''),
            ('HUFFYUV', 'HuffYUV', ''),
            ('MPEG1', 'MPEG-1', ''),
            ('MPEG2', 'MPEG-2', ''),
            ('MPEG4', 'MPEG-4 (divx)', ''),
            ('PNG', 'PNG', ''),
            ('QTRLE', 'QT rle / QT Animation', ''),
            ('THEORA', 'Theora', ''),
            ('WEBM', 'WEBM / VP9', ''),
            ),)

    constant_rate_factor : bpy.props.EnumProperty(
        name='Output Quality',
        default='MEDIUM',
        description='Constant Rate Factor (CRF); tradeoff between video quality and file size',
        items=(
            ('NONE', 'Constant Bitrate', 'Configure constant bit rate, rather than constant output quality'),
            ('LOSSLESS', 'Lossless', ''),
            ('PERC_LOSSLESS', 'Perceptually Lossless', ''),
            ('HIGH', 'High Quality', ''),
            ('MEDIUM', 'Medium Quality', ''),
            ('LOW', 'Low Quality', ''),
            ('VERYLOW', 'Very Low Quality', ''),
            ('LOWEST', 'Lowest Quality', ''),
            ),)

    ffmpeg_preset : bpy.props.EnumProperty(
        name='Encoding Speed',
        default='GOOD',
        description='Tradeoff between encoding speed and compression ratio',
        items=(
            ('BEST', 'Slowest', 'Recommended if you have lots of time and want the best compression efficiency'),
            ('GOOD', 'Good', 'The default and recommended for most applications'),
            ('REALTIME', 'Realtime', 'Recommended for fast encoding'),
            ),)
    
    gopsize : IntProperty(name='Keyframe Interval',
        description='Distance between key frames, also known as GOP size; influences file size and seekability',
        default=18, min=0, max=500, step=1, options={'HIDDEN'})
    
    use_max_b_frames : BoolProperty(name='Use Max B-Frames',
        description='Use Max B-Frames',
        default=False, options={'HIDDEN'})

    max_b_frames : IntProperty(name='Max B-Frames',
        description='Maximum number of B-frames between non-B-frames; influences file size and seekability',
        default=0, min=0, max=16, step=1, options={'HIDDEN'})

    use_lossless_output : BoolProperty(name='Lossless Output',
        description='Use lossless output for video streams',
        default=False, options={'HIDDEN'})

    video_bitrate : IntProperty(
        name='Bitrate',
        default=0,
        description='Video bitrate (kbit/s)',)
    
    minrate : IntProperty(
        name='Min Rate',
        default=0,
        description='Rate control: min rate (kbit/s)',)
    
    maxrate : IntProperty(
        name='Max Rate',
        default=9000,
        description='Rate control: max rate (kbit/s)',)
    
    muxrate : IntProperty(
        name='Mux Rate',
        default=10080000,
        description='Mux rate (bits/second)',)
    
    packetsize : IntProperty(
        name='Mux Packet Size',
        default=2048, min=0, max=16384,
        description='Mux packet size (byte)',)

    buffersize : IntProperty(
        name='Buffersize',
        default=1792, min=0, max=2000,
        description='Rate control: buffer size (kb)',)

    use_autosplit : BoolProperty(
        name='Autosplit Output',
        default=False,
        description='Autosplit output at 2GB boundary',)
    
    ## audio
    audio_codec : EnumProperty(
        name='Audio Codec',
        default='AAC',
        description='FFmpeg audio codec to use',
        items=(
            ('NONE', 'No Audio', 'Disables audio output, for video-only renders'),
            ('AAC', 'AAC', ''),
            ('AC3', 'AC3', ''),
            ('FLAC', 'FLAC', ''),
            ('MP2', 'MP2', ''),
            ('MP3', 'MP3', ''),
            ('OPUS', 'Opus', ''),
            ('PCM', 'PCM', ''),
            ('VORBIS', 'Vorbis', ''),
            ),
        )

    audio_channels : EnumProperty(
        name='Audio Channels',
        default='STEREO',
        description='Audio channel count',
        items=(
            ('MONO', 'Mono', 'Set audio channels to mono'),
            ('STEREO', 'Stereo', 'Set audio channels to stereo'),
            ('SURROUND4', '4 Channels', 'Set audio channels to 4 channels'),
            ('SURROUND51', '5.1 Surround', 'Set audio channels to 5.1 surround sound'),
            ('SURROUND71', '7.1 Surround', 'Set audio channels to 7.1 surround sound'),
            ),
        )
    
    audio_bitrate : IntProperty(
        name='Bitrate',
        default=192, min=32, max=384,
        description='Audio bitrate (kb/s)',)
    
    audio_volume : FloatProperty(
        name='Volume',
        default=1.0, min=0.0, max=1.0,
        description='Audio volume',)
    
    audio_mixrate : IntProperty(
        name='Samplerate',
        default=48000, min=8000, max=192000,
        description='Audio samplerate(samples/s)',)
    

    def draw_vcodec(self, context, layout):
        """Video codec options."""

        layout = layout.column()
        needs_codec = self.format in {'AVI', 'QUICKTIME', 'MKV', 'OGG', 'MPEG4', 'WEBM'}
        if needs_codec:
            layout.prop(self, "codec")

        if needs_codec and self.codec == 'NONE':
            return

        if self.codec == 'DNXHD':
            layout.prop(self, "use_lossless_output")

        # Output quality
        use_crf = needs_codec and self.codec in {'H264', 'MPEG4', 'WEBM'}
        if use_crf:
            layout.prop(self, "constant_rate_factor")

        # Encoding speed
        layout.prop(self, "ffmpeg_preset")
        # I-frames
        layout.prop(self, "gopsize")
        # B-Frames
        row = layout.row(align=True, heading="Max B-frames")
        row.prop(self, "use_max_b_frames", text="")
        sub = row.row(align=True)
        sub.active = self.use_max_b_frames
        sub.prop(self, "max_b_frames", text="")

        if not use_crf or self.constant_rate_factor == 'NONE':
            col = layout.column()

            sub = col.column(align=True)
            sub.prop(self, "video_bitrate")
            sub.prop(self, "minrate", text="Minimum")
            sub.prop(self, "maxrate", text="Maximum")

            col.prop(self, "buffersize", text="Buffer")

            col.separator()

            col.prop(self, "muxrate", text="Mux Rate")
            col.prop(self, "packetsize", text="Mux Packet Size")

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        # layout.use_property_decorate = False
        box = layout.box()
        box.label(text="Direct encode with ffmpeg:")
        col = box.column()
        row = col.row()
        row.label(text="This functionallity need an ffmpeg binary.")
        row.operator('wm.url_open', text='ffmpeg download page', icon='URL').url = 'https://www.ffmpeg.org/download.html'
        
        row = col.row()
        row.label(text="Leave field empty if ffmpeg is in system PATH")
        row.operator('mkvideo.check_ffmpeg', text='Check if ffmpeg in PATH', icon='PLUGIN')
        # col.label(text="May not work if space are in path.")
        box.prop(self, "path_to_ffmpeg")
        
        # ----- Scene settings for new scene creation

        box = layout.box()
        box.label(text="Settings for sequencer creation:")
        ## compact draw (to delete)
        col = box.column()
        col.prop(self, 'file_format')
        row = col.row()
        row.prop(self, 'color_mode', expand=True)

        if self.file_format == 'AVI_JPEG':
            col.prop(self, 'quality')
    
        elif self.file_format == 'FFMPEG':
            col.label(text="Encoding:")
            col.prop(self, 'format')
            col.label(text="Video:")
            self.draw_vcodec(context, box)

            col = box.column()
            col.label(text="Audio:")
            # if self.format != 'MP3':
            col.prop(self, "audio_codec", text="Audio Codec")

            if self.audio_codec != 'NONE':
                col.prop(self, "audio_channels")
                col.prop(self, "audio_mixrate", text="Sample Rate")
                col.prop(self, "audio_bitrate")
                col.prop(self, "audio_volume", slider=True)


def tail_padding(name):
    '''
    return name with a ffmpeg padding marker of 4 digit
    if # found, replace '#' padding by ffmpeg convention
    '''

    # ct = name.count('#')
    if not '#' in name:
        return name + '%04d'
    r = re.search(r'\#{1,10}', name)
    ct = len(r.group())
    return re.sub(r'\#{1,10}', f'%{str(ct).zfill(2)}d', name)


class MKVIDEO_OT_makeVideo(bpy.types.Operator):
    """make video from imgs sequence with ffmpeg"""
    bl_idname = "render.make_video"
    bl_label = "imgs to video"
    bl_options = {'REGISTER'}
    
    def execute(self, context):
        C = bpy.context
        scn = bpy.context.scene

        raw_outpath = scn.render.filepath 
        outfolder = bpy.path.abspath(scn.render.filepath) #get absolute path of output location
        head, tail = os.path.split(outfolder) #split output path

        #get the path in user preferences field
        preferences = context.preferences.addons[__name__].preferences
        path_to_ffmpeg = preferences.path_to_ffmpeg

        binary = "ffmpeg"
        if path_to_ffmpeg:
            if os.path.exists(path_to_ffmpeg) and os.path.isfile(path_to_ffmpeg):
                binary = '"' + path_to_ffmpeg + '"' #surrounding quote doesn't work in win10
            else:
                pathErrorMsg = "wrong path to ffmpeg in the preference of addon " + __name__
                self.report({'ERROR'}, pathErrorMsg)
                return {'CANCELLED'}

        #debug prints
        #print ("path to ffmpeg:", path_to_ffmpeg)
        #print ("raw:", raw_outpath)
        #print ("abs:", outfolder)
        #print ("head:", head)
        #print("norm_head:", os.path.normpath(head))
        #print ("tail:", tail)
        #print ("base:", os.path.basename(head))

        if os.path.exists(head):            
            imgFiles = [i for i in os.listdir(head) if IsImage(head, i)]
            if imgFiles:
                pass
            else:
                missingMessage = "no images in:" + head
                self.report({'ERROR'}, missingMessage)
                return {'CANCELLED'}
        else:
            noPathMessage = "path not exist:" + head
            self.report({'ERROR'}, noPathMessage)
            return {'CANCELLED'}
       
        video_name = "" #override video name output (not used in final addon)
        encode = 'h264' #leave  emlpty quote ("") to encode in mpeg4 codec
        
        quality = 10000
        Qnote = ""
        preset = 'medium'  # preset dispo : ultrafast,superfast, veryfast, faster, fast, medium, slow, slower, veryslow
        if encode == 'h264':
            if scn.MVquality == 'FINAL': #very slow but have great quality with a fair file weight
                preset = 'veryslow'
                quality = 16
                Qnote = "_F"
            elif scn.MVquality == 'NORMAL': #average quality, good compromise between weight and quality
                preset = 'slower'
                quality = 20
            elif scn.MVquality == 'FAST': #fast encoding file against quality.
                preset = 'medium'
                quality = 23
                Qnote = "_L"
            else:
                quality  = 20
                print("no quality settings active! set to preset medium / quality10")

        quality = str(quality)

        #debugs prints
        #print ("_"*10)
        #print ("video output quality set to:", quality)

        if not video_name:
            if tail: #name was specified (name + numbers)
                print ("tail found")
                video_name = tail
                ## if tail ends with "_ - .", then clear it
                # if video_name.endswith(("_","-",".")):
                #     video_name = video_name[:-1]
                video_name = video_name.rstrip(('.#_-'))
            else: #ended on a directory (only numbers)
                print ("no tail")
                video_name = os.path.basename(head)
                print("video_name", video_name)#Dbg
            
        #get framerate
        framerate = str(scn.render.fps)
        ext = scn.render.file_extension

        #get start and end frame
        start = str(scn.frame_start)


        #print('head', head)
        outloc = os.path.normpath(head + "/../")
        if not outloc.endswith(('\\', '/')):
            outloc = outloc + "/"
        print(outloc)

                     
        if Qfix: #suffix file with quality chosen (ex: F/final, L/low/fast/, N/nothing)
            video_name = video_name + Qnote

        check = [i for i in os.listdir(outloc) if i.startswith(video_name) and os.path.isfile(os.path.join(outloc,i))]
        
        if check: #versionning of the file if already exists
            video_name = video_name + "_" + str(len(check) + 1)

        #construct command
        print ("_"*10)        
                
        #pre-assembly
        bypass = ' -y'
        init = binary + ' -f image2 ' + '-start_number ' + start + ' -i'

        srcPath = '"' + head + '/' + tail_padding(tail) + ext + '"'
       
        if encode == 'h264':
            #cmd codec h264 quantizer
            tune = '-r ' + framerate + ' -crf ' + quality + ' -preset ' + preset + ' -pix_fmt yuv420p' + bypass
        else:
            #cmd codec mpeg4 (classic but fast)
            tune = '-r ' + framerate + ' -vcodec mpeg4 -vb ' + quality + 'k' + bypass
        
        destPath = '"' + outloc + video_name + '.mp4"'
        
        #final command assembly
        cmd = init + ' ' + srcPath + ' ' + tune + ' ' + destPath
        print(cmd)
        self.report({'INFO'}, "generating video...")
        print ("_"*10)
        
        #launch
        if subpross:
            if scn.MVopen:
                cmd = cmd + ' && ' + destPath

            cmd_list=shlex.split(cmd)#shlex split keep quotes
            # print(cmd_list)
            subprocess.Popen(cmd_list, shell=False, stderr=subprocess.STDOUT)#shell = True gave problem...

        else:
            startTime = time() #time.time() give the time in second since epoch
            os.system(cmd)
            endTime = time()
            elapsedTime = str(endTime - startTime)
            print ("encoding time :", elapsedTime, "seconds")
            
            outfileloc = os.path.normpath(head + '/../' + video_name + '.mp4')
            message = "video created in: " + outfileloc
            self.report({'INFO'}, message)

            if scn.MVopen:
                #os.system("start " + destPath)
                os.system(destPath)

        return {'FINISHED'}

################## Pannel Integration

def MkVideoPanel(self, context):
    """Video pannels"""
    scn = bpy.context.scene
    layout = self.layout
    layout.use_property_split = True
    split = layout.split(factor=.5, align=True)
    split.prop(scn, 'MVquality')
    split.operator(MKVIDEO_OT_makeVideo.bl_idname, text = "Make video", icon = 'RENDER_ANIMATION') #or icon tiny camera : 'CAMERA_DATA'
    
    row = layout.row(align=False)
    row.prop(scn,'MVrendertrigger')
    row.prop(scn, 'MVopen')


################## Registration


classes = (
imgs2videoPreferences,
MKVIDEO_OT_check_ffmpeg,
MKVIDEO_OT_makeVideo,
MKVIDEO_OT_gen_montage_scene,
)

def register():
    ##  Initialize properties

    bpy.types.Scene.MVquality = bpy.props.EnumProperty(items = [('FINAL', 'Final', 'slower - super quality and optimize weight (add "_F" suffix)'), #[('ENUM1', 'Enum1', 'enum prop 1'),
                                        ('NORMAL', 'Normal', 'good quality and average weight and encoding time'),
                                        ('FAST', 'Fast', 'fast encoding and light weight against quality (add "_L" suffix)')],
                            name="Quality",
                            description="quality settings",
                            default="FINAL")

    bpy.types.Scene.MVrendertrigger = bpy.props.BoolProperty(name = "Auto launch", description = "Automatic trigger after render's end\n", default = False)

    bpy.types.Scene.MVopen = bpy.props.BoolProperty(name = "Open at finish", description = "Open video with player when creation over\n", default = False)


    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.RENDER_PT_output.append(MkVideoPanel)
    bpy.app.handlers.render_complete.append(post_mkvideo)

def unregister():
    if post_mkvideo in bpy.app.handlers.render_complete:
        bpy.app.handlers.render_complete.remove(post_mkvideo) 

    bpy.types.RENDER_PT_output.remove(MkVideoPanel)
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    ##  delete properties
    del bpy.types.Scene.MVquality
    del bpy.types.Scene.MVrendertrigger
    del bpy.types.Scene.MVopen

    
if __name__ == "__main__":
    register()