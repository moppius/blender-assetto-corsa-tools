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

class TextureProperties(bpy.types.PropertyGroup):
    shaderInputName = StringProperty(
        name="Shader Input Name", 
        default = "txDiffuse",
        description ="Name of the shader input slot the texture should be assigned to")


class TexturePanel(bpy.types.Panel):
    bl_label = "Assetto Corsa"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "texture"
    
    @classmethod
    def poll(cls, context):
        if context.texture is not None and context.texture.type == "IMAGE":
            return True
 
    def draw(self, context):
        ac=context.texture.assettoCorsa
        self.layout.prop(ac, "shaderInputName")

def register():
    bpy.types.Texture.assettoCorsa = bpy.props.PointerProperty(type=TextureProperties)
    
def unregister():
    del bpy.types.Texture.assettoCorsa