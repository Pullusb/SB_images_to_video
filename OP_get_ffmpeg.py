import bpy
import sys
import shutil
import zipfile
from pathlib import Path
from . import fn

from bpy.props import (FloatProperty,
                        BoolProperty,
                        EnumProperty,
                        StringProperty,
                        IntProperty,
                        PointerProperty)

## check ffmpeg

class VIDEO_OT_check_ffmpeg(bpy.types.Operator):
    """check if ffmpeg is in path"""
    bl_idname = "video.check_ffmpeg"
    bl_label = "Check ffmpeg bin is available"
    bl_options = {'REGISTER', 'INTERNAL'}
    
    def invoke(self, context, event):
        # check path command
        import shutil
        self.sys_path_ok = shutil.which('ffmpeg')
        
        # check windows exe
        self.local_ffmpeg = False
        self.is_window_os = sys.platform.startswith('win')
        if self.is_window_os:
            ffbin = Path(__file__).parent / 'ffmpeg.exe'
            self.local_ffmpeg = ffbin.exists()

        return context.window_manager.invoke_props_dialog(self, width=250)
    
    def draw(self, context):
        layout = self.layout

        if self.local_ffmpeg:
            layout.label(text='ffmpeg.exe found in addon folder (this binary will be used)', icon='CHECKMARK')
        
        if self.sys_path_ok:
            layout.label(text='ffmpeg is in system PATH', icon='CHECKMARK')
        else:
            layout.label(text='ffmeg is not in system PATH', icon='X') # CANCEL

    def execute(self, context):
        return {'FINISHED'}

## download ffmpeg

def dl_url(url, dest):
    '''download passed url to dest file (include filename)'''
    import urllib.request
    import time
    start_time = time.time()
    with urllib.request.urlopen(url) as response, open(dest, 'wb') as out_file:
        shutil.copyfileobj(response, out_file)
    print(f"Download time {time.time() - start_time:.2f}s",)

def unzip(zip_path, extract_dir_path):
    '''Get a zip path and a directory path to extract to'''
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_dir_path)

class VIDEO_OT_download_ffmpeg(bpy.types.Operator):
    """Download if ffmpeg is in path"""
    bl_idname = "video.download_ffmpeg"
    bl_label = "Download ffmpeg"
    bl_options = {'REGISTER', 'INTERNAL'}
    
    def invoke(self, context, event):
        # Check if an ffmpeg version is already in addon path
        addon_loc = Path(__file__).parent
        self.ff_zip = addon_loc / 'ffmpeg.zip'
        self.ffbin = addon_loc / 'ffmpeg.exe'
        self.exists = self.ffbin.exists()
        return context.window_manager.invoke_props_dialog(self, width=500)
    
    def draw(self, context):
        layout = self.layout
        # layout.label(text='This action will download an ffmpeg release from ffmpeg repository')
        col = layout.column()
        if self.exists:
            col.label(text='ffmpeg is already in addon folder, delete and re-download ? (~90 Mo)', icon='INFO')
        else:
            col.label(text='This will download ffmpeg release from ffmpeg github page in addon folder (~90 Mo)', icon='INFO')
            col.label(text='Would you like to continue ?')

    def execute(self, context):
        if self.exists:
            self.ffbin.unlink()
        
        ## hardcoded compatible release
        release_url = 'https://github.com/BtbN/FFmpeg-Builds/releases/download/autobuild-2021-11-23-12-19/ffmpeg-n4.4.1-2-gcc33e73618-win64-gpl-4.4.zip' 
        dl_url(release_url, str(self.ff_zip))

        with zipfile.ZipFile(str(self.ff_zip), 'r') as zip_ref:
            zip_ffbin = None
            for f in zip_ref.infolist():
                if Path(f.filename).name == 'ffmpeg.exe':
                    zip_ffbin = f
                    break
    
            if zip_ffbin:
                zip_ffbin.filename = Path(zip_ffbin.filename).name
                zip_ref.extract(zip_ffbin, path=str(self.ffbin.parent)) # extract(self, member, path=None, pwd=None)

        if not zip_ffbin:
            self.report({'ERROR'}, 'ffmpeg not found in downloaded zip')
        
        if self.ff_zip.exists():
            self.ff_zip.unlink()
        
        if self.ffbin.exists():
            prefs = fn.get_prefs()
            prefs.path_to_ffmpeg = str(self.ffbin.resolve())

        self.report({'INFO'}, f'Installed: {self.ffbin.resolve()}')
        return {'FINISHED'}

## layout code to add in addon preferences: 
'''
    path_to_ffmpeg : StringProperty(
        name="Path to ffmpeg binary",
        subtype='FILE_PATH')

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        # layout.use_property_decorate = False
        box = layout.box()
        col = box.column()
        # col.label(text="This addon use ffmpeg")
        
        row = col.row()
        row.label(text="This addon need ffmpeg")

        row.operator('wm.url_open', text='FFmpeg Download Page', icon='URL').url = 'https://www.ffmpeg.org/download.html'
        if sys.platform.startswith('win'):
            col.operator('video.download_ffmpeg', text='Auto-install FFmpeg (windows)', icon='IMPORT')

        row = col.row()
        row.label(text="Leave field empty if ffmpeg is in system PATH")
        row.operator('video.check_ffmpeg', text='Check if ffmpeg in PATH', icon='PLUGIN')
        
        # col.label(text="May not work if space are in path.")
        box.prop(self, "path_to_ffmpeg")
'''

classes=(
VIDEO_OT_check_ffmpeg,
VIDEO_OT_download_ffmpeg,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)