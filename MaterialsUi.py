# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# Copyright (C) 2014  Thomas Hagnhofer


import bpy
from bpy.props import *
from . import MaterialsWriter


def convertDictionaryToBlenderEnumItems(dict):
    items=[]
    for key in dict:
        val=str(dict[key])
        items.append((val, key, val))
    return items


class ShaderPropertyItem(bpy.types.PropertyGroup):
    name: StringProperty(name="Property name", default="ksDiffuse")
    valueA: FloatProperty(name="Value A")
    valueB: FloatVectorProperty(name="Value B", size=2)
    valueC: FloatVectorProperty(name="Value C", size=3)
    valueD: FloatVectorProperty(name="Value D", size=4)


class MaterialProperties(bpy.types.PropertyGroup):
    shaderName: StringProperty(
        name="Shader Name",
        default = "ksPerPixel")
    alphaBlendMode: EnumProperty(
        name="Alpha Blend Mode",
        items = convertDictionaryToBlenderEnumItems(MaterialsWriter.BlendMode),
        default = str(MaterialsWriter.BlendMode["Opaque"]))
    alphaTested: BoolProperty(
        name="Alpha Tested",
        default = False)
    depthMode: EnumProperty(
        name="Depth Mode",
        items=convertDictionaryToBlenderEnumItems(MaterialsWriter.DepthMode),
        default = str(MaterialsWriter.DepthMode["DepthNormal"]))
    shaderProperties: CollectionProperty(
        type=ShaderPropertyItem)
    shaderPropertiesActive: IntProperty(
        name="Active Shader Property",
        default=-1)


class KN5_UL_ShaderPropertiesList(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            layout.prop(item,"name", text="", emboss=False)
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.prop(item,"name", text="", emboss=False)


class KN5_PT_MaterialPanel(bpy.types.Panel):
    bl_label = "Assetto Corsa"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "material"

    @classmethod
    def poll(cls, context):
        if context.material is not None:
            return True

    def draw(self, context):
        ac=context.material.assettoCorsa
        self.layout.prop(ac, "shaderName")
        self.layout.prop(ac, "alphaBlendMode")
        self.layout.prop(ac, "alphaTested")
        self.layout.prop(ac, "depthMode")
        shaderBox=self.layout.box()
        shaderBox.label(text="Shader Properties")
        if ac.shaderProperties:
            shaderBox.template_list(
                "KN5_UL_ShaderPropertiesList",
                "",
                ac,
                "shaderProperties",
                ac,
                "shaderPropertiesActive",
                rows=1
            )
            if ac.shaderPropertiesActive >= 0 and ac.shaderPropertiesActive < len(ac.shaderProperties):
                activeProp=ac.shaderProperties[ac.shaderPropertiesActive]
                row=shaderBox.row()
                colA=row.column()
                colA.label(ShaderPropertyItem.valueA[1]["name"])
                colA.prop(activeProp,"valueA", text="")
                colA.prop(activeProp,"valueD")
                colB=row.column()
                colB.prop(activeProp,"valueB")
                colB.prop(activeProp,"valueC")

        row=shaderBox.row()
        row.operator("acmaterialshaderproperties.add")
        row.operator("acmaterialshaderproperties.remove")


class MaterialShaderPropertyAddButton(bpy.types.Operator):
    bl_idname = "acmaterialshaderproperties.add"
    bl_label = "Add Shader Property"

    def execute(self, context):
        ac=context.material.assettoCorsa
        ac.shaderProperties.add()
        return{'FINISHED'}


class MaterialShaderPropertyRemoveButton(bpy.types.Operator):
    bl_idname = "acmaterialshaderproperties.remove"
    bl_label = "Remove Shader Property"

    def execute(self, context):
        ac = context.material.assettoCorsa
        ac.shaderProperties.remove(ac.shaderPropertiesActive)
        return{'FINISHED'}


classes = (
    ShaderPropertyItem,
    MaterialProperties,
    KN5_UL_ShaderPropertiesList,
    KN5_PT_MaterialPanel,
    MaterialShaderPropertyAddButton,
    MaterialShaderPropertyRemoveButton,
)


def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)
    bpy.types.Material.assettoCorsa = bpy.props.PointerProperty(type=MaterialProperties)


def unregister():
    del bpy.types.Material.assettoCorsa
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)
