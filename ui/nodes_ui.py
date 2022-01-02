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
from bpy.props import (
    BoolProperty,
    FloatProperty,
    IntProperty,
)


class NodeProperties(bpy.types.PropertyGroup):
    lodIn: FloatProperty(
        name="LOD In",
        min=0.0,
        unit="LENGTH",
        subtype="DISTANCE",
        description="Nearest distance to the object until it disappears")
    lodOut: FloatProperty(
        name="LOD Out",
        min=0.0,
        unit="LENGTH",
        subtype="DISTANCE",
        description="Farthest distance to the object until it disappears")
    layer: IntProperty(
        name="Layer",
        default=0,
        description="Unknown behaviour")
    castShadows: BoolProperty(
        name="Cast Shadows",
        default=True)
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


class KN5_PT_NodePanel(bpy.types.Panel):
    bl_label = "Assetto Corsa"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"

    @classmethod
    def poll(cls, context):
        return context.object and context.object.type in ["MESH", "CURVE"]

    def draw(self, context):
        ac_obj = context.object.assettoCorsa
        self.layout.prop(ac_obj, "renderable")
        self.layout.prop(ac_obj, "castShadows")
        self.layout.prop(ac_obj, "transparent")
        self.layout.prop(ac_obj, "lodIn")
        self.layout.prop(ac_obj, "lodOut")
        self.layout.prop(ac_obj, "layer")
        self.layout.prop(ac_obj, "visible")


REGISTER_CLASSES = (
    NodeProperties,
    KN5_PT_NodePanel,
)


def register():
    for cls in REGISTER_CLASSES:
        bpy.utils.register_class(cls)
    bpy.types.Object.assettoCorsa = bpy.props.PointerProperty(type=NodeProperties)


def unregister():
    del bpy.types.Object.assettoCorsa
    for cls in reversed(REGISTER_CLASSES):
        bpy.utils.unregister_class(cls)
