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

        settings = scn.mkvideo_prop
        
        binary = fn.ffmpeg_binary(self)
        if not binary:
            return {'CANCELLED'}

        print('binary: ', binary)

        outfolder = bpy.path.abspath(scn.render.filepath) # get absolute path of output location
        if not outfolder:
            self.report({'ERROR'}, 'No output path specified in scene')
            return {'CANCELLED'}

        head, tail = os.path.split(outfolder) # split output path

        ## Check image in output path
        if not fn.contain_images(self, head):
            return {'CANCELLED'}
       
        video_name = "" # override video name output (not used in final addon)
        if not video_name:
            video_name = fn.get_end_stem(context)

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
            video_name = video_name + "_" + str(len(check) + 1).zfill(2)

        sound = False
        # Sound check
        if settings.sound and fn.sound_in_scene():
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
        if sound: # and settings.sound
            sound_cmd = ['-i', audio_path, '-map', '0', '-map', '1', '-shortest'] # <- shortest ?

        cmd = init + src_path + sound_cmd + tune + dest_path

        self.report({'INFO'}, "Generating video...")
        # print ("_"*10)
        
        if sound: # and settings.sound
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
        

        ## shell at True had some problem in the past (needed to chain commands)
        subprocess.Popen(cmd, shell=True, stderr=subprocess.STDOUT)

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
