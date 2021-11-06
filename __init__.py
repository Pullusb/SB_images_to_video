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
    "version": (1, 7, 0),
    "blender": (2, 91, 0),
    "location": "Properties > Render > Output",
    "warning": "",
    "doc_url": "https://github.com/Pullusb/SB_imgs2video/blob/master/README.md",
    "tracker_url": "https://github.com/Pullusb/SB_imgs2video/issues",
    "category": "System" }

import bpy
from bpy.app.handlers import persistent

from . import properties
from . import prefs
from . import OP_mk_vse_montage
from . import OP_mk_ffmpeg_video
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
    ui.register()

    bpy.app.handlers.render_complete.append(post_mkvideo)

def unregister():
    ui.unregister()
    OP_mk_ffmpeg_video.unregister()
    OP_mk_vse_montage.unregister()
    prefs.unregister()
    properties.unregister()

    if post_mkvideo in bpy.app.handlers.render_complete:
        bpy.app.handlers.render_complete.remove(post_mkvideo) 

if __name__ == "__main__":
    register()