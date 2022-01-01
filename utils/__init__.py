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


import json
import os
import struct
import sys
import traceback
import bpy
from inspect import isclass
from bpy.props import BoolProperty, StringProperty
from mathutils import Matrix, Vector, Quaternion


class ReportOperator(bpy.types.Operator):
    bl_idname = "kn5.report_message"
    bl_label = "Export report"

    isError: BoolProperty()
    title: StringProperty()
    message: StringProperty()

    def execute(self, context):
        if self.isError:
            self.report({'WARNING'}, self.message)
        else:
            self.report({'INFO'}, self.message)
        return {'FINISHED'}

    def invoke(self, context, event):
        self.execute(context)
        wm = context.window_manager
        return wm.invoke_popup(self, width=600)

    def draw(self, context):
        if self.isError:
            self.layout.alert = True
        row = self.layout.row()
        row.alignment="CENTER"
        row.label(text=self.title)
        for line in self.message.splitlines():
            row=self.layout.row()
            line=line.replace("\t"," "*4)
            row.label(text=line)
        row = self.layout.row()
        row.operator("kn5.report_clipboard").content=self.message


class CopyClipboardButtonOperator(bpy.types.Operator):
    bl_idname = "kn5.report_clipboard"
    bl_label = "Copy to clipboard"

    content: StringProperty()

    def execute(self, context):
        context.window_manager.clipboard = self.content
        return {'FINISHED'}

    def invoke(self, context, event):
        self.execute(context)
        return {'FINISHED'}


def convertMatrix(m):
    co, rotation, scale=m.decompose()
    co=convertVector3(co)
    rotation=convertQuaternion(rotation)
    mat_loc = Matrix.Translation(co)
    mat_sca = Matrix.Scale(scale[0],4,(1,0,0)) * Matrix.Scale(scale[2],4,(0,1,0)) * Matrix.Scale(scale[1],4,(0,0,1))
    mat_rot = rotation.to_matrix().to_4x4()
    return mat_loc * mat_rot * mat_sca


def convertVector3(v):
    return Vector((v[0], v[2], -v[1]))


def convertQuaternion(q):
    axis, angle = q.to_axis_angle()
    axis = convertVector3(axis)
    return Quaternion(axis, angle)


def readSettings(file):
    fullPath=os.path.abspath(file)
    dirName=os.path.dirname(fullPath)
    settingsPath=os.path.join(dirName, "settings.json")
    if not os.path.exists(settingsPath):
        return {}
    return json.loads(open(settingsPath, "r").read())


def getActiveMaterialTextureSlot(material):
    if material and material.node_tree:
        for node in material.node_tree.nodes:
            if isinstance(node, classbpy.types.TextureNodeImage):
                return node
    #for textureIndex in range(0, len(material.texture_slots)):
    #    if material.texture_slots[textureIndex] is not None and material.texture_slots[textureIndex].use:
    #       return material.texture_slots[textureIndex]
    return None


def register_recursive(objects):
    """Registers classes with Blender recursively from modules."""
    for obj in objects:
        if isclass(obj):
            bpy.utils.register_class(obj)
        elif hasattr(obj, "register"):
            obj.register()
        elif hasattr(obj, "REGISTER_CLASSES"):
            register_recursive(obj.REGISTER_CLASSES)
        else:
            print(f"Warning: Failed to find anything to register for '{obj}'")


def unregister_recursive(objects):
    """Unregisters classes from Blender recursively from modules."""
    for obj in reversed(objects):
        if isclass(obj):
            bpy.utils.unregister_class(obj)
        elif hasattr(obj, "unregister"):
            obj.unregister()
        elif hasattr(obj, "REGISTER_CLASSES"):
            unregister_recursive(obj.REGISTER_CLASSES)
        else:
            print(f"Warning: Failed to find anything to unregister for '{obj}'")
