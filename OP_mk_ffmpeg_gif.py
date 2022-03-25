from email.policy import default
import bpy
import os
import subprocess
from bpy_extras.io_utils import ImportHelper
from pathlib import Path
from . import fn

class MKVIDEO_OT_make_gif(bpy.types.Operator):
    """make gif from exported sequence with ffmpeg"""
    bl_idname = "render.make_gif"
    bl_label = "Imgs To Gifs"
    bl_options = {'REGISTER'}

    # frame rate
    fps : bpy.props.IntProperty(name='Frame Rate',default=15, min=1, max=500,
    description='Frame rate of outputed gif')

    # quality mode
    quality_on_diff : bpy.props.BoolProperty(name='Movement Over Static Background',default=True,
    description='Prioritize quality of moving part (diff mode instead of full)\nOften better when pixels are moving over a static background')

    # change size (0 == no change)
    width : bpy.props.IntProperty(name='Width', default=0, min=0,
    description='Scale gif size based on given width (0 = no scaling)', subtype='PIXEL')

    # export multiple gifs wioth different settings to compare quality/weight
    multi_exports : bpy.props.BoolProperty(name='Multi Exports', default=False,
    description='Export 16 differents labeled gifs with all possible settings to pick the best looking one')

    dithering : bpy.props.EnumProperty(
    name="Dithering", description="Dithering option (default is sierra2_4a)",
    default='sierra2_4a',
    items=(
        ('none', 'none', 'No dithering', 0),   
        ('floyd_steinberg', 'floyd_steinberg', 'floyd_steinberg (error diffusal dithering)', 1),   
        ('sierra2_4a', 'sierra2_4a', 'sierra2_4a (error diffusal dithering)', 2),   
        ('bayer', 'bayer', 'Bayer (predictable dithering)', 3),   
        ('bayer:bayer_scale=2', 'bayer2', 'Bayer (predictable dithering) with crosshatch pattern increase by 2', 4),   
        ('bayer:bayer_scale=3', 'bayer3', 'Bayer (predictable dithering) with crosshatch pattern increase by 3', 5),   
        ('bayer:bayer_scale=4', 'bayer4', 'Bayer (predictable dithering) with crosshatch pattern increase by 4', 6),   
        ('bayer:bayer_scale=5', 'bayer5', 'Bayer (predictable dithering) with crosshatch pattern increase by 5', 7),   
        ))

    def invoke(self, context, event):
        scn = context.scene
        if self.fps == 15: # use scene fps instead of default
            self.fps = scn.render.fps
        
        self.settings = scn.mkvideo_prop
        self.prefs = fn.get_prefs()

        self.binary = fn.ffmpeg_binary(self)
        if not self.binary:
            return {'CANCELLED'}

        outfolder = bpy.path.abspath(scn.render.filepath) # get absolute path of output location
        if not outfolder:
            self.report({'ERROR'}, 'No output path specified in scene')
            return {'CANCELLED'}
        head, tail = os.path.split(outfolder) # split output path

        if not fn.contain_images(self, head):
            return {'CANCELLED'}

        return context.window_manager.invoke_props_dialog(self) # width=500
    
    def draw(self, context):
        layout = self.layout
        # layout.use_property_split = True
        col = layout.column()
        col.prop(self, 'fps')
        col.prop(self, 'width')
        # if self.width == 0:
        col.label(text='Width 0 = No rescale')

        setting_col = layout.column()
        setting_col.prop(self, 'quality_on_diff')
        setting_col.prop(self, 'dithering')

        col = layout.column()
        col.prop(self, 'multi_exports')
        setting_col.active = not self.multi_exports


    def execute(self, context):
        scn = bpy.context.scene
        outfolder = bpy.path.abspath(scn.render.filepath) # get absolute path of output location
        head, tail = os.path.split(outfolder) # split output path

        gif_name = fn.get_end_stem(context)
        
        # get start and end frame
        start = str(scn.frame_start)

        outloc = Path(head).parent
        
        # versionning of the file if already exists
        if not self.multi_exports:
            # in case of multi-export keep original name
            check = [i for i in os.scandir(outloc) if i.name.startswith(gif_name) and i.is_file()]
            if check: # add filecount + 1
                gif_name = gif_name + "_" + str(len(check) + 1).zfill(2)

        ext = scn.render.file_extension
        # Construct commnand
        init = [self.binary, '-f', 'image2', '-start_number', start, '-i']

        src_path = Path(head) / (fn.tail_padding(tail) + ext)
        gif = outloc / (gif_name + '.gif')

        # fps filter
        filters = f'fps={self.fps}'

        # optional scale filter
        if self.width:
            # scalar flags default is bilinear, but lanczos or bicubic are way better (sharper)
            filters += f',scale={self.width}:-1:flags=lanczos'

        ## case of multi-exports
        if self.multi_exports:
            # create a dest folder
            out_folder = gif.parent / (gif.stem + '_gif_batch')
            out_folder.mkdir(exist_ok=True)
            gif = out_folder / gif.name
            
            d_list = ['none', 'floyd_steinberg', 'sierra2_4a', 'bayer', 
            'bayer:bayer_scale=2', 'bayer:bayer_scale=3', 'bayer:bayer_scale=4', 'bayer:bayer_scale=5']

            for stats_mode in ['=stats_mode=full', '=stats_mode=diff']:
                
                for d_mode in d_list:
                    dither_mode = f'=dither={d_mode}'

                    setting_s = '_' + d_mode.replace(':bayer_scale=', '') + '_' + stats_mode.replace('=stats_mode=', '')
                    new_path = gif.with_name(gif.stem + setting_s + '.gif')

                    full_filters = filters + f',split[s0][s1];[s0]palettegen{stats_mode}[p];[s1][p]paletteuse{dither_mode}'
                    cmd = init + [str(src_path), '-vf', full_filters, '-loop', '0', '-y', str(new_path)]
                    
                    print(f'Export {new_path.name} :', ' '.join(cmd))
                    subprocess.call(cmd) 

            return {'FINISHED'}

        # set stat and complete filter
        stats_mode = '=stats_mode=diff' if self.quality_on_diff else ''
        dither_mode = '=dither=' + self.dithering

        full_filters = filters + f',split[s0][s1];[s0]palettegen{stats_mode}[p];[s1][p]paletteuse{dither_mode}'

        cmd = init + [str(src_path), '-vf', full_filters] + ['-loop', '0', '-y', str(gif)]

        self.report({'INFO'}, "Generating gif...")

        print('-- ffmpeg command --')
        print(' '.join(cmd))

        error = subprocess.call(cmd, shell=True)
        
        ## shell at True had some problem in the past (needed to chain commands)
        # if self.settings.open:
        #     cmd += ['&&'] + str(gif)
        # subprocess.Popen(cmd, shell=True, stderr=subprocess.STDOUT)

        if not error and self.settings.open:
            # open the file
            subprocess.Popen([str(gif)], shell=True, stderr=subprocess.STDOUT)
        return {'FINISHED'}

class MKVIDEO_OT_make_gif_from_folder(bpy.types.Operator, ImportHelper):
    """Create a gif scene from a chosen folder / numbered image sequence / video file"""
    bl_idname = "render.make_gif_from_folder"
    bl_label = "Gif From Path"
    bl_options = {'REGISTER'}

    fps : bpy.props.IntProperty(name='Frame Rate',default=15, min=1, max=500,
    description='Frame rate of outputed gif')

    # change size (0 == no change)
    width : bpy.props.IntProperty(name='Width', default=0, min=0,
    description='Scale gif size based on given width (0 = no scaling)', subtype='PIXEL')

    # export multiple gifs wioth different settings to compare quality/weight
    multi_exports : bpy.props.BoolProperty(name='Multi Exports', default=False,
    description='Export 16 differents labeled gifs with all possible settings to pick the best looking one')
    
    # quality mode
    quality_on_diff : bpy.props.BoolProperty(name='Movement Over Static Background',default=True,
    description='Prioritize quality of moving part (diff mode instead of full)\nOften better when pixels are moving over a static background')

    dithering : bpy.props.EnumProperty(
    name="Dithering", description="Dithering option (default is sierra2_4a)",
    default='sierra2_4a',
    items=(
        ('none', 'none', 'No dithering', 0),   
        ('floyd_steinberg', 'floyd_steinberg', 'floyd_steinberg (error diffusal dithering)', 1),   
        ('sierra2_4a', 'sierra2_4a', 'sierra2_4a (error diffusal dithering)', 2),   
        ('bayer', 'bayer', 'Bayer (predictable dithering)', 3),   
        ('bayer:bayer_scale=2', 'bayer2', 'Bayer (predictable dithering) with crosshatch pattern increase by 2', 4),   
        ('bayer:bayer_scale=3', 'bayer3', 'Bayer (predictable dithering) with crosshatch pattern increase by 3', 5),   
        ('bayer:bayer_scale=4', 'bayer4', 'Bayer (predictable dithering) with crosshatch pattern increase by 4', 6),   
        ('bayer:bayer_scale=5', 'bayer5', 'Bayer (predictable dithering) with crosshatch pattern increase by 5', 7),   
        ))
    
    # directory = bpy.props.StringProperty(subtype='DIR_PATH')
    
    filepath : bpy.props.StringProperty(
        name="File Path", 
        description="File path used for import", 
        maxlen= 1024)
    
    def execute(self, context):
        # fp = context.scene.render.filepath
        
        self.binary = fn.ffmpeg_binary(self)
        if not self.binary:
            return {'CANCELLED'}
        settings = context.scene.mkvideo_prop

        fp = self.filepath
        print('fp: ', fp)

        outpath = Path(fp)
        
        if outpath.is_file():
            outfolder = outpath.parent
            outloc = outfolder.parent
            files = [outpath]
        else:
            outfolder = outpath
            outloc = outpath.parent
            files = fn.get_files(outpath) # list of scandir entry

        ## check if file is a video
        
        video_src = fn.is_video(outpath)

        if video_src:
            outloc = outfolder # output in existing_file
            gif = outloc / (outpath.stem + '.gif')
            init = [self.binary, '-i']
            src_path = outpath
        
        else: 
            if not files:
                self.report({'ERROR'}, f'No numerated file in {outfolder}')
                return {'CANCELLED'}

            gif_name = outfolder.stem # directly use end folder as name

            # versionning of the file if already exists
            if not self.multi_exports:
                # in case of multi-export keep original name
                check = [i for i in os.scandir(outloc) if i.name.startswith(gif_name) and i.is_file()]
                if check: # add filecount + 1
                    gif_name = gif_name + "_" + str(len(check) + 1).zfill(2)

            check = [i.name for i in os.scandir(outfolder.parent) if i.name.startswith(gif_name) and i.is_file()]
            if check: # versionning of the file if already exists
                gif_name = gif_name + "_" + str(len(check) + 1).zfill(2)
            
            # Construct commnand
            init = [self.binary, '-f', 'image2', '-start_number', str(int(fn.righmost_number(files[0].name))), '-i']

            src_path = outfolder / fn.get_ffmpeg_padding_marker(files[0].name)
            gif = outloc / (gif_name + '.gif')

        # fps filter
        filters = f'fps={self.fps}'

        # optional scale filter
        if self.width:
            # scalar flags default is bilinear, but lanczos or bicubic are way better (sharper)
            filters += f',scale={self.width}:-1:flags=lanczos'

        ## case of multi-exports
        if self.multi_exports:
            # create a dest folder
            if video_src:
                out_folder = gif.with_name(gif.stem + '_gif_batch') # in same folder as video
            else:
                out_folder = gif.parent / (gif.stem + '_gif_batch') # one folder above img sequence

            out_folder.mkdir(exist_ok=True)
            gif = out_folder / gif.name
            
            d_list = ['none', 'floyd_steinberg', 'sierra2_4a', 'bayer', 
            'bayer:bayer_scale=2', 'bayer:bayer_scale=3', 'bayer:bayer_scale=4', 'bayer:bayer_scale=5']

            for stats_mode in ['=stats_mode=full', '=stats_mode=diff']:
                
                for d_mode in d_list:
                    dither_mode = f'=dither={d_mode}'

                    setting_s = '_' + d_mode.replace(':bayer_scale=', '') + '_' + stats_mode.replace('=stats_mode=', '')
                    new_path = gif.with_name(gif.stem + setting_s + '.gif')

                    full_filters = filters + f',split[s0][s1];[s0]palettegen{stats_mode}[p];[s1][p]paletteuse{dither_mode}'
                    cmd = init + [str(src_path), '-vf', full_filters, '-loop', '0', '-y', str(new_path)]
                    
                    print(f'Export {new_path.name} :', ' '.join(cmd))
                    subprocess.call(cmd) 

            return {'FINISHED'}

        # set stat and complete filter
        stats_mode = '=stats_mode=diff' if self.quality_on_diff else ''
        dither_mode = '=dither=' + self.dithering

        full_filters = filters + f',split[s0][s1];[s0]palettegen{stats_mode}[p];[s1][p]paletteuse{dither_mode}'

        cmd = init + [str(src_path), '-vf', full_filters] + ['-loop', '0', '-y', str(gif)]

        self.report({'INFO'}, "Generating gif...")

        print('-- ffmpeg command --')
        print(' '.join(cmd))
        print()
        error = subprocess.call(cmd, shell=True)

        if not error and settings.open:
            # open the file
            subprocess.Popen([str(gif)], shell=True, stderr=subprocess.STDOUT)

        return {'FINISHED'}


classes = (
MKVIDEO_OT_make_gif,
MKVIDEO_OT_make_gif_from_folder
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
