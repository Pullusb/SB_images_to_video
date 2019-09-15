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
    "description": "generate a video from image sequence in output folder",
    "author": "Samuel Bernou ",
    "version": (1, 3, 1),
    "blender": (2, 77, 0),
    "location": "Properties > Render > Output",
    "warning": "",
    "wiki_url": "",
    "category": "System" }

import bpy, os, re
from bpy.app.handlers import persistent
from time import time


################## Initialize properties

bpy.types.Scene.MVquality = bpy.props.EnumProperty(items = [('FINAL', 'Final', 'slower - super quality and optimize weight (add "_F" suffix)'), #[('ENUM1', 'Enum1', 'enum prop 1'),
                                    ('NORMAL', 'Normal', 'good quality and average weight and encoding time'),
                                    ('FAST', 'Fast', 'fast encoding and light weight against quality (add "_L" suffix)')],
                           name="Quality",
                           description="quality settings",
                           default="FINAL")

bpy.types.Scene.MVrendertrigger = bpy.props.BoolProperty(name = "Auto launch", description = "Automatic trigger after render's end\n", default = False)

bpy.types.Scene.MVopen = bpy.props.BoolProperty(name = "Open at finish", description = "Open video with player when creation over\n", default = False)

Qfix = True #bool add suffix to name with quality
subpross= True
################## functions and operators

@persistent
def post_mkvideo(scene):
    #if auto-launch is ticked
    if scene.MVrendertrigger:
        #launch mk video
        bpy.ops.render.mk_video_operator()


def IsImage(head, i):
    if not os.path.isfile(os.path.join(head,i)):
        return False
    imgsTypeList = ["PNG", "JPG", "BMP", "TIFF", "JPEG"]
    for ext in imgsTypeList:
        if i.upper().endswith(ext):
            return (True)
    return (False)

class imgs2videoPreferences(bpy.types.AddonPreferences):
    bl_idname = __name__

    path_to_ffmpeg = bpy.props.StringProperty(
        name="Path to ffmpeg binary",
        subtype='FILE_PATH',
        )

    def draw(self, context):
        layout = self.layout
        layout.label(
            text="This addon need an ffmpeg binary. "
                 "Leave the field empty if ffmpeg is in your PATH."
                 " May not work if space are in path.")
        layout.prop(self, "path_to_ffmpeg")


class MkVideoOperator(bpy.types.Operator):
    """make video from imgs sequence with ffmpeg"""
    bl_idname = "render.mk_video_operator"
    bl_label = "imgs to video"
    bl_options = {'REGISTER'}
    
    def execute(self, context):
        C = bpy.context
        scn = bpy.context.scene

        raw_outpath = scn.render.filepath 
        outfolder = bpy.path.abspath(scn.render.filepath) #get absolute path of output location
        head, tail = os.path.split(outfolder) #split output path

        #get the path in user preferences field
        preferences = context.user_preferences.addons[__name__].preferences
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
                #if tail ends with "_ - .", then clear it
                if video_name.endswith("_") or video_name.endswith("-") or video_name.endswith("."):
                    video_name = video_name[:-1]
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
        srcPath = '"' + head + '/' + tail + '%04d' + ext + '"'
       
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
            import subprocess
            import shlex

            if scn.MVopen:
                cmd = cmd + ' && ' + destPath

            cmd_list=shlex.split(cmd)#shlex split keep quotes
            # print(cmd_list)
            subprocess.Popen(cmd_list, shell=True, stderr=subprocess.STDOUT)

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
    split = layout.split(percentage=.5, align=True)
    split.prop(scn, 'MVquality')
    split.operator(MkVideoOperator.bl_idname, text = "Make video", icon = 'RENDER_ANIMATION') #or icon tiny camera : 'CAMERA_DATA'
    
    row = layout.row(align=False)
    row.prop(scn,'MVrendertrigger')
    row.prop(scn, 'MVopen')


################## Registration

def register():
    bpy.utils.register_class(imgs2videoPreferences)
    bpy.utils.register_class(MkVideoOperator)
    bpy.types.RENDER_PT_output.append(MkVideoPanel)
    bpy.app.handlers.render_complete.append(post_mkvideo)

def unregister():
    if post_mkvideo in bpy.app.handlers.render_complete:
        bpy.app.handlers.render_complete.remove(post_mkvideo) 
    bpy.utils.unregister_class(MkVideoOperator)
    bpy.types.RENDER_PT_output.remove(MkVideoPanel)
    bpy.utils.unregister_class(imgs2videoPreferences)

    
if __name__ == "__main__":
    register()