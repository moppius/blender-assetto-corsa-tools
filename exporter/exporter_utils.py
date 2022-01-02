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
import bpy
from mathutils import Matrix, Quaternion, Vector


def convert_matrix(in_matrix):
    co, rotation, scale = in_matrix.decompose()
    co = convert_vector3(co)
    rotation = convert_quaternion(rotation)
    mat_loc = Matrix.Translation(co)
    mat_scale_1 = Matrix.Scale(scale[0], 4, (1, 0, 0))
    mat_scale_2 = Matrix.Scale(scale[2], 4, (0, 1, 0))
    mat_scale_3 = Matrix.Scale(scale[1], 4, (0, 0, 1))
    mat_scale = mat_scale_1 @ mat_scale_2 @ mat_scale_3
    mat_rot = rotation.to_matrix().to_4x4()
    return mat_loc @ mat_rot @ mat_scale


def convert_vector3(in_vec):
    return Vector((in_vec[0], in_vec[2], -in_vec[1]))


def convert_quaternion(in_quat):
    axis, angle = in_quat.to_axis_angle()
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
    full_path = os.path.abspath(file)
    dir_name = os.path.dirname(full_path)
    settings_path = os.path.join(dir_name, "settings.json")
    if not os.path.exists(settings_path):
        return {}
    return json.loads(open(settings_path, "r").read())
