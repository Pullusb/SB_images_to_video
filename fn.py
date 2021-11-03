import bpy
import os
import re
from pathlib import Path

def get_prefs():
    return bpy.context.preferences.addons[__package__].preferences


### ffmpeg video functions

def is_image(head, i):
    if not os.path.isfile(os.path.join(head,i)):
        return False
    imgsTypeList = ["png", "jpg", "bmp", "tiff", "jpeg", "exr", "tga"]
    for ext in imgsTypeList:
        if i.lower().endswith(ext):
            return True
    return False

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


### VSE creation functions


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