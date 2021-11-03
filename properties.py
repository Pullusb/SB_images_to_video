import bpy
from bpy.props import (StringProperty,
                        IntProperty,
                        BoolProperty,
                        EnumProperty,
                        FloatProperty)

class MKVIDEO_PGT_settings(bpy.types.PropertyGroup):

    quality : EnumProperty(
        name="Quality",
        description="quality settings",
        default="FINAL",
        items = (
            ('FINAL', 'Final', 'slower - super quality and optimize weight (add "_F" suffix)'), #[('ENUM1', 'Enum1', 'enum prop 1'),
            ('NORMAL', 'Normal', 'good quality and average weight and encoding time'),
            ('FAST', 'Fast', 'fast encoding and light weight against quality (add "_L" suffix)')
            ),
    )

    rendertrigger : BoolProperty(
        name="Auto Launch", default=False,
        description = "Automatic trigger after render's end\n",
        )

    open : BoolProperty(
        name="Open At Finish", default=False,
        description = "Open video with player when creation over\n",
        )

def register():
    bpy.utils.register_class(MKVIDEO_PGT_settings)
    bpy.types.Scene.mkvideo_prop = bpy.props.PointerProperty(type = MKVIDEO_PGT_settings)


def unregister():
    del bpy.types.Scene.mkvideo_prop
    bpy.utils.unregister_class(MKVIDEO_PGT_settings)
