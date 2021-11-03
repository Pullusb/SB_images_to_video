# Changelog

1.6.0

- code: huge refactor. True multifile mode.
- ui: added montge scene creation button
- fix: scene creation operator when scene exists

1.5.0

- feat: new montage mode (beta, basic behavior), generate a scene where the sequence you just rendered are imported in VSE

1.4.0 - 2021-11-01

- code: switch from to multifile addon
- doc: removed old 2.7 version and add link to _old addons_ repo

8/01/2020

- handle padding in filename (e.g: img_####) correctly
- shell True -> False in subprocess Popen. has problem on a linux machine

15/09/2019

- 2.8 version yay !

03/03/2017

- Subprocess !  Blender is no more locked during the encoding, you're free to continue the work !

07/04/2016

- removed useless "resize" functionnality (causing problem with some ffmpeg version)
- added "auto launch" tickbox, allow to auto trigger the file creation after rendering