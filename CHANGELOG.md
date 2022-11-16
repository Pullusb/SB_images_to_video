# Changelog

2.3.2

- fix: sound strip creation in montage scene

2.3.1

- fix: new arg restriction sound strip creation

2.3.0

- added: `from folder` option allow to load a video instead of image sequence only

2.2.0

- added: new `make gif from path`. Can generate gif from chosen _folder / sequence / video_ chosen from filebrowser

2.1.0

- added: new `make gif` feature. Generate optimized gif (pop-up panel with gif settings including a multi-export)

2.0.0

- ui: Improved readability
  - Placed in a subpanel of output
  - Separate vidually ffmpeg encode and sequencer creation
  - Expose sound output selection (seem)
- fix: Error preventing use of ffmpeg in Path
- added: prefill output for generated sequencer scene
- changed: video version increment on re-encode with a padding of two

1.9.0

- feat: VSE from folder. Create a sequencer scene directly from a chosen sequence directory
  - Resolution will be set automatically from first image
  - scene is name after the folder's name (with suffix "_edit")

1.8.0

- feat: if no ffmpeg found, pop-up a window to do in addon pref
- feat: ffmpeg can be auto-downloaded (windows) from addon preferences

1.7.0

- feat: Auto mix down audio in generated video (When audio strip in VSE or Speaker in Scene)
- code: Use now directly list to subprocess

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