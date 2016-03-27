# SB_imgs2video

Add buttons in Blender UI to create a video from just rendered images sequence in one click

[DEMO](https://youtu.be/R_W3Uh3KVGM)

--------


Description:

Add 4 buttons in the Properties>Output pannel

When your render as image sequence is finished just hit "make video"

the resize option take only the width of the scene in account and keep ratio (percentage is not considered) on some version of ffmpeg this option may not work (it is recommanded to open your console before launching)

screenshot:

![Output pannel with imgs2video Addon enabled](http://www.samuelbernou.fr/imgs/git/Addon_imgs2video_screenshot_demo)

TODO:

-Currently blender freeze during the operation (not using subprocess)

-Set fine tune settings for 3D image in the presets.


