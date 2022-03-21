# SPDX-License-Identifier: GPL-2.0-or-later

bl_info = {
    "name": "Images to Video",
    "description": "Generate a video from image sequence",
    "author": "Samuel Bernou",
    "version": (2, 1, 0),
    "blender": (2, 91, 0),
    "location": "Properties > Render > Output",
    "doc_url": "https://github.com/Pullusb/SB_images_to_video/blob/master/README.md",
    "tracker_url": "https://github.com/Pullusb/SB_images_to_video/issues",
    "category": "System" }

import bpy
from bpy.app.handlers import persistent

from . import properties
from . import prefs
from . import OP_mk_vse_montage
from . import OP_mk_ffmpeg_video
from . import OP_mk_ffmpeg_gif
from . import OP_get_ffmpeg
from . import ui

@persistent
def post_mkvideo(scene):
    #if auto-launch is ticked
    if scene.mkvideo_prop.rendertrigger:
        bpy.ops.render.make_video()

def register():
    properties.register()
    prefs.register()
    OP_mk_vse_montage.register()
    OP_mk_ffmpeg_video.register()
    OP_mk_ffmpeg_gif.register()
    OP_get_ffmpeg.register()
    ui.register()

    bpy.app.handlers.render_complete.append(post_mkvideo)

def unregister():
    ui.unregister()
    OP_get_ffmpeg.unregister()
    OP_mk_ffmpeg_gif.unregister()
    OP_mk_ffmpeg_video.unregister()
    OP_mk_vse_montage.unregister()
    prefs.unregister()
    properties.unregister()

    if post_mkvideo in bpy.app.handlers.render_complete:
        bpy.app.handlers.render_complete.remove(post_mkvideo) 

if __name__ == "__main__":
    register()