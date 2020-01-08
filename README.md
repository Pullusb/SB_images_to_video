# SB_imgs2video

Add buttons in Blender UI to create a video from just rendered images sequence in one click

[DEMO Youtube](https://youtu.be/R_W3Uh3KVGM)  
  
**[Download latest](https://raw.githubusercontent.com/Pullusb/SB_imgs2video/master/SB_imgs2video.py)** (right click, save Target as)

**[Download older (2.7)](https://raw.githubusercontent.com/Pullusb/SB_imgs2video/master/SB_imgs2video_279.py)** (right click, save Target as)
  
--------


Description:

Add 4 buttons in the Properties>Output pannel

When your image sequence render is finished, just choose the quality and hit *"make video"*.
In the last version the resize option was replaced by an auto trigger tickbox, allowing to create the video automatically after the render.

Choose between 3 preset:
- Fast - fast encoding and light weight against quality (add "_L" suffix)
- normal - good quality, average weight and encoding time
- Final - slower - super quality and optimize weight (add "_F" suffix)

screenshot:

![Output pannel with imgs2video Addon enabled](http://www.samuelbernou.fr/imgs/git/Addon_imgs2video_screenshot_demo)

TODO:

-Set fine tune settings for 3D image in the presets.

#### Update 8/01/2020

- handle padding in filename (e.g: img_####) correctly
- shell True -> False in subprocess Popen. has problem on a linux machine

#### Update 15/09/2019

- 2.8 version yay !

#### Update 03/03/2017

- Subprocess !  Blender is no more locked during the encoding, you're free to continue the work !

#### Update 07/04/2016
- removed useless "resize" functionnality (causing problem with some ffmpeg version)
- added "auto launch" tickbox, allow to auto trigger the file creation after rendering
