import bpy
import os
from pathlib import Path
import subprocess
from . import fn

class MKVIDEO_OT_makeVideo(bpy.types.Operator):
    """make video from imgs sequence with ffmpeg"""
    bl_idname = "render.make_video"
    bl_label = "imgs to video"
    bl_options = {'REGISTER'}
    
    def execute(self, context):
        scn = bpy.context.scene

        prefs = fn.get_prefs()
        
        # get the path in user preferences field
        path_to_ffmpeg = prefs.path_to_ffmpeg
        
        settings = scn.mkvideo_prop

        outfolder = bpy.path.abspath(scn.render.filepath) # get absolute path of output location
        head, tail = os.path.split(outfolder) # split output path

        binary = "ffmpeg"
        if path_to_ffmpeg:
            if os.path.exists(path_to_ffmpeg) and os.path.isfile(path_to_ffmpeg):
                binary = path_to_ffmpeg
            else:
                self.report({'ERROR'}, "Wrong path to ffmpeg in the preference of addon")
                return {'CANCELLED'}

        if os.path.exists(head):            
            imgFiles = [i for i in os.listdir(head) if fn.is_image(head, i)]
            if imgFiles:
                pass
            else:
                self.report({'ERROR'}, f'no images in: {head}')
                return {'CANCELLED'}
        else:
            self.report({'ERROR'}, f'path not exist: {head}')
            return {'CANCELLED'}
       
        video_name = "" # override video name output (not used in final addon)
        encode = 'h264' # leave  emlpty quote ("") to encode in mpeg4 codec
        
        quality = 10000
        Qnote = ""
        preset = 'medium' # preset dispo : ultrafast,superfast, veryfast, faster, fast, medium, slow, slower, veryslow
        if encode == 'h264':
            if settings.quality == 'FINAL': #very slow but have great quality with a fair file weight
                preset = 'veryslow'
                quality = 16
                Qnote = "_F"
            elif settings.quality == 'NORMAL': #average quality, good compromise between weight and quality
                preset = 'slower'
                quality = 20
            elif settings.quality == 'FAST': #fast encoding file against quality.
                preset = 'medium'
                quality = 23
                Qnote = "_L"
            else:
                quality  = 20
                print("no quality settings active! set to preset medium / quality10")

        quality = str(quality)

        if not video_name:
            if tail: #name was specified (name + numbers)
                print ("tail found")
                video_name = tail
                ## if tail ends with "_ - .", then clear it
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
                     
        if prefs.note_suffix: #suffix file with quality chosen (ex: F/final, L/low/fast/, N/nothing)
            video_name = video_name + Qnote

        check = [i for i in os.listdir(outloc) if i.startswith(video_name) and os.path.isfile(os.path.join(outloc,i))]
        
        if check: #versionning of the file if already exists
            video_name = video_name + "_" + str(len(check) + 1)

        sound = False
        # Sound check
        if fn.sound_in_scene():
            # Mix down audio
            print('sound detected in scene')
            audio_path = f'{outloc}scn_audio.wav'
            audio_path = str(Path(audio_path))
            print('audio_path: ', audio_path)
            ret = bpy.ops.sound.mixdown('INVOKE_DEFAULT',
                filepath=audio_path, check_existing=False, relative_path=False, container='WAV', codec='PCM', format='S16')
            if 'FINISHED' in ret:
                sound = True
                
        # Construct commnand
        bypass = '-y'
        init = [binary, '-f', 'image2', '-start_number', start, '-i']

        src_path = [head + '/' + fn.tail_padding(tail) + ext]
       
        if encode == 'h264':
            #cmd codec h264 quantizer
            tune = ['-r', framerate, '-crf', quality, '-preset', preset, '-pix_fmt', 'yuv420p', bypass]
        else:
            #cmd codec mpeg4 (classic but fast)
            tune = ['-r', framerate, '-vcodec', 'mpeg4', '-vb', f'{quality}k', bypass]
        
        dest_path = [outloc + video_name + '.mp4']
        
        sound_cmd = []
        if sound:
            sound_cmd = ['-i', audio_path, '-map', '0', '-map', '1', '-shortest'] # <- shortest ?

        cmd = init + src_path + sound_cmd + tune + dest_path

        self.report({'INFO'}, "Generating video...")
        # print ("_"*10)
        
        if sound:
            ## add delete temporary sound command (depending on filesystem)
            my_os = fn.detect_OS()
            if my_os == 'windows':
                cmd += ['&&', 'del', audio_path]
            else:
                cmd += ['&&', 'rm', audio_path]

        if settings.open:
            cmd += ['&&'] + dest_path

        print('-- ffmpeg command --')
        print(' '.join(cmd))
        if sound:
            subprocess.Popen(cmd, shell=True, stderr=subprocess.STDOUT)
        else:
            subprocess.Popen(cmd, shell=False, stderr=subprocess.STDOUT) # shell = True gave problem in older version...

        return {'FINISHED'}


classes = (
MKVIDEO_OT_makeVideo,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
