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
        options= {'HIDDEN'},
    )

    rendertrigger : BoolProperty(
        name="Encode At Render End", default=False,
        description = "Automatic trigger after render's end\n",
        options= {'HIDDEN'},
        )

    open : BoolProperty(
        name="Play Video After Encode", default=True,
        description = "Open video with default system player when encoding is over\n",
        options= {'HIDDEN'},
        )
    
    sound : BoolProperty(
        name="Sound", default=True,
        description = "Mix sound of VSE/Scene into generated video",
        options= {'HIDDEN'},
        )

def register():
    bpy.utils.register_class(MKVIDEO_PGT_settings)
    bpy.types.Scene.mkvideo_prop = bpy.props.PointerProperty(type = MKVIDEO_PGT_settings)


def unregister():
    del bpy.types.Scene.mkvideo_prop
    bpy.utils.unregister_class(MKVIDEO_PGT_settings)
