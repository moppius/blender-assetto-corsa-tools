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


class NodeProperties(bpy.types.PropertyGroup):
    lodIn: FloatProperty(
        name="LOD In",
        min=0.0,
        unit="LENGTH",
        subtype="DISTANCE",
        description="Nearest distance to the object until it disapears")
    lodOut: FloatProperty(
        name="LOD Out",
        min=0.0,
        unit="LENGTH",
        subtype="DISTANCE",
        description="Farthest distance to the object until it disapears")
    layer: IntProperty(
        name="Layer",
        default = 0,
        description="Unknown behaviour")
    castShadows: BoolProperty(
        name="Cast Shadows",
        default = True)
    visible: BoolProperty(
        name="Visible",
        default=True,
        description="Unknown behaviour")
    transparent: BoolProperty(
        name="Transparent",
        default=False)
    renderable: BoolProperty(
        name="Renderable",
        default=True,
        description="Toggles if the object should be rendered or not")


class NodePanel(bpy.types.Panel):
    bl_label = "Assetto Corsa"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"

    @classmethod
    def poll(cls, context):
        if context.object is not None and context.object.type == "MESH":
            return True

    def draw(self, context):
        ac=context.object.assettoCorsa
        self.layout.prop(ac, "renderable")
        self.layout.prop(ac, "castShadows")
        self.layout.prop(ac, "transparent")
        self.layout.prop(ac, "lodIn")
        self.layout.prop(ac, "lodOut")
        self.layout.prop(ac, "layer")
        self.layout.prop(ac, "visible")


classes = (
    NodeProperties,
    NodePanel,
)


def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)
    bpy.types.Object.assettoCorsa = bpy.props.PointerProperty(type=NodeProperties)


def unregister():
    del bpy.types.Object.assettoCorsa
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)
