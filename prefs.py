import bpy, os, re, sys
from pathlib import Path
from time import time
import subprocess
import shlex

from . import fn
from bpy.props import (StringProperty,
                        IntProperty,
                        BoolProperty,
                        EnumProperty,
                        FloatProperty)

class imgs2videoPreferences(bpy.types.AddonPreferences):
    bl_idname = __package__

    path_to_ffmpeg : StringProperty(
        name="Path to ffmpeg binary",
        subtype='FILE_PATH',)

    note_suffix : BoolProperty(
        default=True,
        name="Suffix note (L-F)",
        description="suffix file with quality chosen (F/final, L/low/fast/)"
    ) # N/nothing,)

    ## Stored preferences for video scene settings
    
    file_format : EnumProperty(
        name='File Format',
        items=(
            ('AVI_JPEG', 'AVI JPEG', 'Output video in AVI JPEG format'),
            ('AVI_RAW', 'AVI Raw', 'Output video in AVI Raw format'),
            ('FFMPEG', 'FFmpeg Video', 'The most versatile way to output video files'),
        ),
        default='FFMPEG',
        description='File format to save the rendered images as',
    )

    color_mode : EnumProperty(
        name='Color Mode',
        default='RGB',
        description='Choose BW for saving grayscale, RGB for saving red, green and blue channels, and RGBA for saving red, green, blue and alpha channels',
        items=(
            ('BW', 'BW', 'grayscale'),
            ('RGB', 'RGB', 'RGB (color) data'),
            ),)

    quality : IntProperty(name="Quality",
        description="Quality for format with loss compression",
        default=90, min=0, max=100, step=1, subtype='PERCENTAGE', options={'HIDDEN'})

    format : EnumProperty(
        name='Container',
        default='MKV',
        description='Output file container',
        items=(
            ('MPEG1', 'MPEG-1', ''),
            ('MPEG2', 'MPEG-2', ''),
            ('MPEG4', 'MPEG-4', ''),
            ('AVI', 'AVI', ''),
            ('QUICKTIME', 'Quicktime', ''),
            ('DV', 'DV', ''),
            ('OGG', 'Ogg', ''),
            ('MKV', 'Matroska', ''),
            ('FLASH', 'Flash', ''),
            ('WEBM', 'WebM', ''),
            ),)

    codec : EnumProperty(
        name='Video Codec',
        default='H264',
        description='FFmpeg codec to use for video output',
        items=(
            ('NONE', 'No Video', 'Disables video output, for audio-only renders'),
            ('DNXHD', 'DNxHD', ''),
            ('DV', 'DV', ''),
            ('FFV1', 'FFmpeg video codec #1', ''),
            ('FLASH', 'Flash Video', ''),
            ('H264', 'H.264', ''),
            ('HUFFYUV', 'HuffYUV', ''),
            ('MPEG1', 'MPEG-1', ''),
            ('MPEG2', 'MPEG-2', ''),
            ('MPEG4', 'MPEG-4 (divx)', ''),
            ('PNG', 'PNG', ''),
            ('QTRLE', 'QT rle / QT Animation', ''),
            ('THEORA', 'Theora', ''),
            ('WEBM', 'WEBM / VP9', ''),
            ),)

    constant_rate_factor : bpy.props.EnumProperty(
        name='Output Quality',
        default='MEDIUM',
        description='Constant Rate Factor (CRF); tradeoff between video quality and file size',
        items=(
            ('NONE', 'Constant Bitrate', 'Configure constant bit rate, rather than constant output quality'),
            ('LOSSLESS', 'Lossless', ''),
            ('PERC_LOSSLESS', 'Perceptually Lossless', ''),
            ('HIGH', 'High Quality', ''),
            ('MEDIUM', 'Medium Quality', ''),
            ('LOW', 'Low Quality', ''),
            ('VERYLOW', 'Very Low Quality', ''),
            ('LOWEST', 'Lowest Quality', ''),
            ),)

    ffmpeg_preset : bpy.props.EnumProperty(
        name='Encoding Speed',
        default='GOOD',
        description='Tradeoff between encoding speed and compression ratio',
        items=(
            ('BEST', 'Slowest', 'Recommended if you have lots of time and want the best compression efficiency'),
            ('GOOD', 'Good', 'The default and recommended for most applications'),
            ('REALTIME', 'Realtime', 'Recommended for fast encoding'),
            ),)
    
    gopsize : IntProperty(name='Keyframe Interval',
        description='Distance between key frames, also known as GOP size; influences file size and seekability',
        default=18, min=0, max=500, step=1, options={'HIDDEN'})
    
    use_max_b_frames : BoolProperty(name='Use Max B-Frames',
        description='Use Max B-Frames',
        default=False, options={'HIDDEN'})

    max_b_frames : IntProperty(name='Max B-Frames',
        description='Maximum number of B-frames between non-B-frames; influences file size and seekability',
        default=0, min=0, max=16, step=1, options={'HIDDEN'})

    use_lossless_output : BoolProperty(name='Lossless Output',
        description='Use lossless output for video streams',
        default=False, options={'HIDDEN'})

    video_bitrate : IntProperty(
        name='Bitrate',
        default=0,
        description='Video bitrate (kbit/s)',)
    
    minrate : IntProperty(
        name='Min Rate',
        default=0,
        description='Rate control: min rate (kbit/s)',)
    
    maxrate : IntProperty(
        name='Max Rate',
        default=9000,
        description='Rate control: max rate (kbit/s)',)
    
    muxrate : IntProperty(
        name='Mux Rate',
        default=10080000,
        description='Mux rate (bits/second)',)
    
    packetsize : IntProperty(
        name='Mux Packet Size',
        default=2048, min=0, max=16384,
        description='Mux packet size (byte)',)

    buffersize : IntProperty(
        name='Buffersize',
        default=1792, min=0, max=2000,
        description='Rate control: buffer size (kb)',)

    use_autosplit : BoolProperty(
        name='Autosplit Output',
        default=False,
        description='Autosplit output at 2GB boundary',)
    
    ## audio
    audio_codec : EnumProperty(
        name='Audio Codec',
        default='AAC',
        description='FFmpeg audio codec to use',
        items=(
            ('NONE', 'No Audio', 'Disables audio output, for video-only renders'),
            ('AAC', 'AAC', ''),
            ('AC3', 'AC3', ''),
            ('FLAC', 'FLAC', ''),
            ('MP2', 'MP2', ''),
            ('MP3', 'MP3', ''),
            ('OPUS', 'Opus', ''),
            ('PCM', 'PCM', ''),
            ('VORBIS', 'Vorbis', ''),
            ),
        )

    audio_channels : EnumProperty(
        name='Audio Channels',
        default='STEREO',
        description='Audio channel count',
        items=(
            ('MONO', 'Mono', 'Set audio channels to mono'),
            ('STEREO', 'Stereo', 'Set audio channels to stereo'),
            ('SURROUND4', '4 Channels', 'Set audio channels to 4 channels'),
            ('SURROUND51', '5.1 Surround', 'Set audio channels to 5.1 surround sound'),
            ('SURROUND71', '7.1 Surround', 'Set audio channels to 7.1 surround sound'),
            ),
        )
    
    audio_bitrate : IntProperty(
        name='Bitrate',
        default=192, min=32, max=384,
        description='Audio bitrate (kb/s)',)
    
    audio_volume : FloatProperty(
        name='Volume',
        default=1.0, min=0.0, max=1.0,
        description='Audio volume',)
    
    audio_mixrate : IntProperty(
        name='Samplerate',
        default=48000, min=8000, max=192000,
        description='Audio samplerate(samples/s)',)
    

    def draw_vcodec(self, context, layout):
        """Video codec options."""

        layout = layout.column()
        needs_codec = self.format in {'AVI', 'QUICKTIME', 'MKV', 'OGG', 'MPEG4', 'WEBM'}
        if needs_codec:
            layout.prop(self, "codec")

        if needs_codec and self.codec == 'NONE':
            return

        if self.codec == 'DNXHD':
            layout.prop(self, "use_lossless_output")

        # Output quality
        use_crf = needs_codec and self.codec in {'H264', 'MPEG4', 'WEBM'}
        if use_crf:
            layout.prop(self, "constant_rate_factor")

        # Encoding speed
        layout.prop(self, "ffmpeg_preset")
        # I-frames
        layout.prop(self, "gopsize")
        # B-Frames
        row = layout.row(align=True, heading="Max B-frames")
        row.prop(self, "use_max_b_frames", text="")
        sub = row.row(align=True)
        sub.active = self.use_max_b_frames
        sub.prop(self, "max_b_frames", text="")

        if not use_crf or self.constant_rate_factor == 'NONE':
            col = layout.column()

            sub = col.column(align=True)
            sub.prop(self, "video_bitrate")
            sub.prop(self, "minrate", text="Minimum")
            sub.prop(self, "maxrate", text="Maximum")

            col.prop(self, "buffersize", text="Buffer")

            col.separator()

            col.prop(self, "muxrate", text="Mux Rate")
            col.prop(self, "packetsize", text="Mux Packet Size")

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        # layout.use_property_decorate = False
        box = layout.box()
        box.label(text="Direct encode with ffmpeg:")
        col = box.column()
        row = col.row()
        row.label(text="This functionallity need an ffmpeg binary.")
        row.operator('wm.url_open', text='ffmpeg download page', icon='URL').url = 'https://www.ffmpeg.org/download.html'
        
        row = col.row()
        row.label(text="Leave field empty if ffmpeg is in system PATH")
        row.operator('video.check_ffmpeg', text='Check ffmpeg', icon='PLUGIN')
        if sys.platform.startswith('win'):
            row = col.row()
            row.label(text="FFmpeg can be automatically downloaded")
            row.operator('video.download_ffmpeg', text='Auto-install FFmpeg (windows)', icon='IMPORT')
        
        # col.label(text="May not work if space are in path.")
        box.prop(self, "path_to_ffmpeg")
        
        # ----- Scene settings for new scene creation

        box = layout.box()
        box.label(text="Settings for sequencer creation:")
        ## compact draw (to delete)
        col = box.column()
        col.prop(self, 'file_format')
        row = col.row()
        row.prop(self, 'color_mode', expand=True)

        if self.file_format == 'AVI_JPEG':
            col.prop(self, 'quality')
    
        elif self.file_format == 'FFMPEG':
            col.label(text="Encoding:")
            col.prop(self, 'format')
            col.label(text="Video:")
            self.draw_vcodec(context, box)

            col = box.column()
            col.label(text="Audio:")
            # if self.format != 'MP3':
            col.prop(self, "audio_codec", text="Audio Codec")

            if self.audio_codec != 'NONE':
                col.prop(self, "audio_channels")
                col.prop(self, "audio_mixrate", text="Sample Rate")
                col.prop(self, "audio_bitrate")
                col.prop(self, "audio_volume", slider=True)


class MKVIDEO_OT_open_addon_prefs(bpy.types.Operator):
    bl_idname = "mkvideo.open_addon_prefs"
    bl_label = "Open Addon Prefs"
    bl_description = "Open user preferences window in addon tab and prefill the search with addon name"
    bl_options = {"REGISTER"}

    def execute(self, context):
        fn.open_addon_prefs()
        return {'FINISHED'}

classes = (
MKVIDEO_OT_open_addon_prefs,
imgs2videoPreferences,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
