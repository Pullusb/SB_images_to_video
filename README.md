# SB_imgs2video

Add buttons in Blender UI to create a video from just rendered images sequence in one click

[DEMO](https://youtu.be/R_W3Uh3KVGM)

--------


Description:

Add 4 buttons in the Properties>Output pannel

When your render as image sequence is finished just hit "make video".
In the last version the resize option was replaced by an auto trigger tickbox, allowing to create a video right after the render.

screenshot:

![Output pannel with imgs2video Addon enabled](http://www.samuelbernou.fr/imgs/git/Addon_imgs2video_screenshot_demo)

TODO:

-Currently blender freeze during the operation (not using subprocess)

-Set fine tune settings for 3D image in the presets.



#### Update 07/04/2016
- removed useless "resize" functionnality (causing problem with some ffmpeg version)
- added "auto launch" tickbox, allow to auto trigger the file creation after rendering
