import bpy
import os
import re
from pathlib import Path

def get_prefs():
    return bpy.context.preferences.addons[__package__].preferences

def open_addon_prefs():
    '''Open addon prefs windows with focus on current addon'''
    from .__init__ import bl_info
    wm = bpy.context.window_manager
    wm.addon_filter = 'All'
    if not 'COMMUNITY' in  wm.addon_support: # reactivate community
        wm.addon_support = set([i for i in wm.addon_support] + ['COMMUNITY'])
    wm.addon_search = bl_info['name']
    bpy.context.preferences.active_section = 'ADDONS'
    bpy.ops.preferences.addon_expand(module=__package__)
    bpy.ops.screen.userpref_show('INVOKE_DEFAULT')

def detect_OS():
    """return str of os name : linux, windows, mac (None if undetected)"""
    from sys import platform
    myOS = platform

    if myOS.startswith('linux') or myOS.startswith('freebsd'):# linux
        return ("linux")

    elif myOS.startswith('win'):# Windows
        return ("windows")

    elif myOS == "darwin":# OS X
        return ('mac')

    else:# undetected
        print("Cannot detect OS, python 'sys.platform' give :", myOS)
        return None

def show_message_box(_message = "", _title = "Message Box", _icon = 'INFO'):
    '''Show message box with element passed as string or list
    if _message if a list of lists:
        if sublist have 2 element:
            considered a label [text,icon]
        if sublist have 3 element:
            considered as an operator [ops_id_name, text, icon]
    '''

    def draw(self, context):
        for l in _message:
            if isinstance(l, str):
                self.layout.label(text=l)
            else:
                if len(l) == 2: # label with icon
                    self.layout.label(text=l[0], icon=l[1])
                elif len(l) == 3: # ops
                    self.layout.operator_context = "INVOKE_DEFAULT"
                    self.layout.operator(l[0], text=l[1], icon=l[2], emboss=False) # <- True highligh the entry
    
    if isinstance(_message, str):
        _message = [_message]
    bpy.context.window_manager.popup_menu(draw, title = _title, icon = _icon)

### ffmpeg video functions

def is_image(head, i):
    if not os.path.isfile(os.path.join(head,i)):
        return False
    imgsTypeList = ["png", "jpg", "bmp", "tiff", "jpeg", "exr", "tga"]
    for ext in imgsTypeList:
        if i.lower().endswith(ext):
            return True
    return False

def is_video(fp):
    fp = Path(fp)
    if not fp.is_file():
        return False
    videoTypeList = ["mp4", "mov", "mkv", "webm", "avi",
    "wmv", "avchd", "flv", "f4v", "swf",
    "m4a", "3gp", "3g2", "mj2"]

    return bool([x for x in videoTypeList if fp.name.lower().endswith('.' + x)])

def righmost_number(name) -> str:
    '''Return righ mmost number is past string, None if no number found'''
    res = re.search(r'(\d+)(?!.*\d)', str(name))
    if res:
        return res.group(1)


def tail_padding(name):
    '''
    return name with a ffmpeg padding marker of 4 digit
    if # found, replace '#' padding by ffmpeg convention
    '''

    if not '#' in name:
        return name + '%04d'
    r = re.search(r'\#{1,10}', name)
    ct = len(r.group())
    return re.sub(r'\#{1,10}', f'%{str(ct).zfill(2)}d', name)

def get_ffmpeg_padding_marker(name):
    '''return name with righmost number replaced by ffmpeg padding marker'''
    return re.sub(r'(\d+)(?!.*\d)', lambda x : f"%{str(len(x.group(1))).zfill(2)}d", str(name))


### VSE creation functions


def get_next_available_channel(scn=None, start_from=1):
    '''return available channel starting from chosen index'''
    scn = scn or bpy.context.scene
    vse = scn.sequence_editor
    used_channel = tuple([s.channel for s in vse.sequences_all])
    for i in range(start_from, 256):
        if not i in used_channel:
            return i

def get_files(outpath, name_filter=False):
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

    if name and name_filter:
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
        name=strip_name, filepath=files[0].path, channel=channel, frame_start=start_frame, fit_method='ORIGINAL')
    ## fit method in  ('FIT', 'FILL', 'STRETCH', 'ORIGINAL') default : 'ORIGINAL'
    for img in files[1:]:
       seq.elements.append(img.name)
    
    return seq

def add_video_to_scene(scn, fp, strip_name=None, channel=None, start_frame=None):
    '''Set video on scn from fp'''
    vse = scn.sequence_editor
    if start_frame is None:
        start_frame = scn.frame_start

    if not channel:
        channel = get_next_available_channel(scn=scn, start_from=1)

    outpath = os.path.abspath(bpy.path.abspath(fp))

    if not strip_name:
        strip_name = outpath.name
    
    strip = vse.sequences.new_movie(
        name=strip_name, filepath=str(outpath), channel=channel, frame_start=start_frame, fit_method='ORIGINAL')
    ## fit method in  ('FIT', 'FILL', 'STRETCH', 'ORIGINAL') default : 'ORIGINAL'
    return strip

def sound_in_scene():
    scn = bpy.context.scene
    vse = scn.sequence_editor
    if vse and any(s.type == 'SOUND' and not s.mute for s in vse.sequences_all):
        return True
    if any(o.type == 'SPEAKER' and not o.hide_viewport and o.data and o.data.sound and not o.data.muted for o in scn.objects):
        return True
    return False


### -- using self
## Check ffmpeg binary to use

def ffmpeg_binary(self):
    # get the path in user preferences field
    prefs = get_prefs()
    path_to_ffmpeg = prefs.path_to_ffmpeg

    ## get ffmpeg bin
    ffbin = Path(__file__).parent / 'ffmpeg.exe'

    if path_to_ffmpeg:
        if os.path.exists(path_to_ffmpeg) and os.path.isfile(path_to_ffmpeg):
            return path_to_ffmpeg
        else:
            self.report({'ERROR'}, "Wrong path to ffmpeg in the preference of addon")
            return # {'CANCELLED'}        
    
    elif detect_OS() == 'windows' and ffbin.exists():
        print('-- using ffmpeg found in addon folder')
        return str(ffbin)
    
    else:
        import shutil
        if not shutil.which('ffmpeg'):
            show_message_box(_title = "No ffmpeg found", _icon = 'INFO',
                _message =[
                        "ffmpeg is needed for this action, see addon prefs",
                        ["mkvideo.open_addon_prefs", "Click here to open addon prefs", "PREFERENCES"] # TOOL_SETTINGS
                    ])
            return # {'CANCELLED'}
        return "ffmpeg"
    

def contain_images(self, fp):

    if not os.path.exists(fp):
        self.report({'ERROR'}, f'path not exist: {fp}')
        return False
    
    imgFiles = [i for i in os.listdir(fp) if is_image(fp, i)]
    if imgFiles:
        pass
    else:
        self.report({'ERROR'}, f'no images in: {fp}')
        return False

    return True

def get_end_stem(context):
    outfolder = bpy.path.abspath(context.scene.render.filepath) # get absolute path of output location
    head, tail = os.path.split(outfolder) # split output path
    if tail: #name was specified (name + numbers)
        print ("tail found")
        ## if tail ends with "_ - .", then clear it
        return tail.rstrip(('.#_-'))
    else: #ended on a directory (only numbers)
        print ("no tail")
        return os.path.basename(head)