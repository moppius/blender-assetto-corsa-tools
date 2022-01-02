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
import bpy
from mathutils import Matrix, Quaternion, Vector


def convert_matrix(m):
    co, rotation, scale = m.decompose()
    co = convert_vector3(co)
    rotation = convert_quaternion(rotation)
    mat_loc = Matrix.Translation(co)
    mat_scale_1 = Matrix.Scale(scale[0], 4, (1,0,0))
    mat_scale_2 = Matrix.Scale(scale[2], 4, (0,1,0))
    mat_scale_3 = Matrix.Scale(scale[1], 4, (0,0,1))
    mat_scale = mat_scale_1 @ mat_scale_2 @ mat_scale_3
    mat_rot = rotation.to_matrix().to_4x4()
    return mat_loc @ mat_rot @ mat_scale


def convert_vector3(v):
    return Vector((v[0], v[2], -v[1]))


def convert_quaternion(q):
    axis, angle = q.to_axis_angle()
    axis = convert_vector3(axis)
    return Quaternion(axis, angle)


def get_texture_nodes(material):
    texture_nodes = []
    if material.node_tree:
        for node in material.node_tree.nodes:
            if isinstance(node, bpy.types.ShaderNodeTexImage):
                texture_nodes.append(node)
    return texture_nodes


def get_all_texture_nodes(context):
    scene_texture_nodes = []
    for obj in context.blend_data.objects:
        if obj.type != "MESH":
            continue
        for slot in obj.material_slots:
            if slot.material:
                scene_texture_nodes.extend(get_texture_nodes(slot.material))
    return scene_texture_nodes


def get_active_material_texture_slot(material):
    texture_nodes = get_texture_nodes(material)
    for texture_node in texture_nodes:
        if texture_node.show_texture:
            return texture_node
    return None


def read_settings(file):
    fullPath=os.path.abspath(file)
    dirName=os.path.dirname(fullPath)
    settingsPath=os.path.join(dirName, "settings.json")
    if not os.path.exists(settingsPath):
        return {}
    return json.loads(open(settingsPath, "r").read())
