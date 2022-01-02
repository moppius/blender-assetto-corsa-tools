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


import math
import os
import re
import bmesh
from mathutils import Matrix
from .exporter_utils import (
    convert_matrix,
    convert_vector3,
    get_active_material_texture_slot,
)
from .kn5_writer import KN5Writer
from ..utils.constants import ASSETTO_CORSA_OBJECTS


NodeClass = {
    "Node" : 1,
    "Mesh" : 2,
    "SkinnedMesh" : 3,
}


NODES = "nodes"


class NodeWriter(KN5Writer):
    def __init__(self, file, context, settings, warnings, material_writer):
        super().__init__(file)

        self.context = context
        self.settings = settings
        self.warnings = warnings
        self.material_writer = material_writer
        self.scene = self.context.scene
        self.node_settings = []
        self._init_assetto_corsa_objects()
        self._init_node_settings()

    def _init_node_settings(self):
        self.node_settings = []
        if NODES in self.settings:
            for nodeKey in self.settings[NODES]:
                self.node_settings.append(node_settings(self.settings, nodeKey))

    def _init_assetto_corsa_objects(self):
        self.acObjects=[]
        for o in ASSETTO_CORSA_OBJECTS:
            self.acObjects.append(re.compile(f"^{o}$"))

    def _is_ac_object(self, name):
        for regex in self.acObjects:
            if regex.match(name):
                return True
        return False

    def write(self):
        self._write_base_node(None, "BlenderFile")
        for o in sorted(self.context.blend_data.objects, key=lambda k: len(k.children)):
            if not o.parent:
                self._write_object(o)

    def _write_object(self, obj):
        if not obj.name.startswith("__"):
            if obj.type == "MESH":
                if len(obj.children) != 0:
                    raise Exception(f"A mesh cannot contain children ('{obj.name}')")
                self._write_mesh_node(obj)
            else:
                self._write_base_node(obj, obj.name)
            for child in obj.children:
                self._write_object(child)

    def _any_child_is_mesh(self, obj):
        for child in obj.children:
            if child.type in ["MESH", "CURVE"] or self._any_child_is_mesh(child):
                return True
        return False

    def _write_base_node(self, obj, node_name):
        node_data = {}
        matrix = None
        num_children = 0
        if not obj:
            matrix = Matrix()
            for o in self.context.blend_data.objects:
                if not o.parent and not o.name.startswith("__"):
                    num_children += 1
        else:
            if not self._is_ac_object(obj.name) and not self._any_child_is_mesh(obj):
                self.warnings.append(f"Unknown logical object '{obj.name}' might prevent other objects from loading.{os.linesep}\tRename it to '__{obj.name}' if you do not want to export it.")
            matrix = convert_matrix(obj.matrix_local)
            for child in obj.children:
                if not child.name.startswith("__"):
                    num_children += 1

        node_data["name"] = node_name
        node_data["childCount"] = num_children
        node_data["active"] = True
        node_data["transform"] = matrix
        self._write_base_node_data(node_data)

    def _write_base_node_data(self, node_data):
        self._write_node_class("Node")
        self.write_string(node_data["name"])
        self.write_uint(node_data["childCount"])
        self.write_bool(node_data["active"])
        self.write_matrix(node_data["transform"])

    def _write_mesh_node(self, obj):
        divided_meshes = self._split_object_by_materials(obj)
        divided_meshes = self._split_meshes_for_vertex_limit(divided_meshes)
        if obj.parent or len(divided_meshes) > 1:
            node_data = {}
            node_data["name"] = obj.name
            node_data["childCount"] = len(divided_meshes)
            node_data["active"] = True
            transformMatrix = Matrix()
            if obj.parent:
                transformMatrix = convert_matrix(obj.parent.matrix_world.inverted())
            node_data["transform"] = transformMatrix
            self._write_base_node_data(node_data)
        nodeProperties = NodeProperties(obj)
        for nodeSetting in self.node_settings:
            nodeSetting.apply_settings_to_node(nodeProperties)
        for mesh in divided_meshes:
            self._write_mesh(obj, mesh, nodeProperties)

    def _write_node_class(self, nodeClass):
        self.write_uint(NodeClass[nodeClass])

    def _write_mesh(self, obj, mesh, nodeProperties):
        self._write_node_class("Mesh")
        self.write_string(obj.name)
        self.write_uint(0) # Child count, none allowed
        is_active = True
        self.write_bool(is_active)
        self.write_bool(nodeProperties.castShadows)
        self.write_bool(nodeProperties.visible)
        self.write_bool(nodeProperties.transparent)
        if len(mesh.vertices) > 2**16:
            raise Exception(f"Only {2**16} vertices per mesh allowed. ('{obj.name}')")
        self.write_uint(len(mesh.vertices))
        for v in mesh.vertices:
            self.write_vector3(v.co)
            self.write_vector3(v.normal)
            self.write_vector2(v.uv)
            self.write_vector3(v.tangent)
        self.write_uint(len(mesh.indices))
        for i in mesh.indices:
            self.write_ushort(i)
        if mesh.material_id is None:
            self.warnings.append(f"No material to mesh '{obj.name}' assigned")
            self.write_uint(0)
        else:
            self.write_uint(mesh.material_id)
        self.write_uint(nodeProperties.layer) #Layer
        self.write_float(nodeProperties.lodIn) #LOD In
        self.write_float(nodeProperties.lodOut) #LOD Out
        self._write_bounding_sphere(mesh.vertices)
        self.write_bool(nodeProperties.renderable) #isRenderable

    def _write_bounding_sphere(self, vertices):
        max_x = -999999999
        max_y = -999999999
        max_z = -999999999
        min_x = 999999999
        min_y = 999999999
        min_z = 999999999
        for v in vertices:
            co = v.co
            if co[0] > max_x:
               max_x = co[0]
            if co[0] < min_x:
               min_x = co[0]
            if co[1] > max_y:
               max_y = co[1]
            if co[1] < min_y:
               min_y = co[1]
            if co[2] > max_z:
               max_z = co[2]
            if co[2] < min_z:
               min_z = co[2]

        sphere_center = [
            min_x + (max_x - min_x) / 2,
            min_y + (max_y - min_y) / 2,
            min_z + (max_z - min_z) / 2
        ]
        sphere_radius = max((max_x - min_x) / 2, (max_y - min_y) / 2, (max_z - min_z) / 2) * 2
        self.write_vector3(sphere_center)
        self.write_float(sphere_radius)

    def _split_object_by_materials(self, obj):
        meshes = []
        mesh_copy = obj.to_mesh()

        bm = bmesh.new()
        bm.from_mesh(mesh_copy)
        bmesh.ops.triangulate(bm, faces=bm.faces[:])
        bm.to_mesh(mesh_copy)
        bm.free()

        try:
            uv_layer = mesh_copy.uv_layers.active
            mesh_copy.calc_loop_triangles()
            mesh_copy.calc_tangents()
            mesh_vertices = mesh_copy.vertices[:]
            mesh_loops = mesh_copy.loops[:]
            mesh_triangles = mesh_copy.loop_triangles[:]
            matrix = obj.matrix_world

            if not mesh_copy.materials:
                raise Exception(f"Object '{obj.name}' has no material assigned")

            used_materials = set([triangle.material_index for triangle in mesh_triangles])
            for material_index in used_materials:
                if not mesh_copy.materials[material_index]:
                    raise Exception(f"Material slot {material_index} for object '{obj.name}' has no material assigned")
                material_name = mesh_copy.materials[material_index].name
                if material_name.startswith("__") :
                    raise Exception(f"Material '{material_name}' is ignored but is used by object '{obj.name}'")

                vertices = {}
                indices = []
                for triangle in mesh_triangles:
                    if material_index != triangle.material_index:
                        continue
                    vertexIndexForFace = 0
                    face_indices = []
                    for loop_index in triangle.loops:
                        loop = mesh_loops[loop_index]
                        local_position = matrix @ mesh_vertices[loop.vertex_index].co
                        converted_position = convert_vector3(local_position)
                        converted_normal = convert_vector3(loop.normal)
                        uv = (0, 0)
                        if uv_layer:
                            uv = uv_layer.data[triangle.index].uv
                            uv = (uv[0], -uv[1])
                        else:
                            uv = self._calculate_uvs(obj, mesh_copy, material_index, local_position)
                        tangent = loop.tangent
                        vertex = UvVertex(converted_position, converted_normal, uv, tangent)
                        if not vertex in vertices:
                            newIndex = len(vertices)
                            vertices[vertex] = newIndex
                        face_indices.append(vertices[vertex])
                        vertexIndexForFace += 1
                    indices.extend((face_indices[1], face_indices[2], face_indices[0]))
                    if len(face_indices) == 4:
                        indices.extend((face_indices[2], face_indices[3], face_indices[0]))
                vertices = [v for v, index in sorted(vertices.items(), key=lambda k: k[1])]
                material_id = self.material_writer.material_positions[material_name]
                meshes.append(Mesh(material_id, vertices, indices))
        finally:
            obj.to_mesh_clear()
        return meshes

    def _split_meshes_for_vertex_limit(self, divided_meshes):
        new_meshes = []
        limit = 2**16
        for mesh in divided_meshes:
            if len(mesh.vertices) > limit:
                start_index = 0
                while start_index < len(mesh.indices):
                    vertex_index_mapping = {}
                    new_indices = []
                    for i in range(start_index, len(mesh.indices), 3):
                        start_index += 3
                        face = mesh.indices[i:i+3]
                        for face_index in face:
                            if not face_index in vertex_index_mapping:
                                newIndex = len(vertex_index_mapping)
                                vertex_index_mapping[face_index] = newIndex
                            new_indices.append(vertex_index_mapping[face_index])
                        if len(vertex_index_mapping) >= limit-3:
                            break
                    vertices = [mesh.vertices[v] for v, index in sorted(vertex_index_mapping.items(), key=lambda k: k[1])]
                    new_meshes.append(Mesh(mesh.material_id, vertices, new_indices))
            else:
                new_meshes.append(mesh)
        return new_meshes

    def _calculate_uvs(self, obj, mesh, material_id, co):
        size = obj.dimensions
        x = co[0] / size[0]
        y = co[1] / size[1]
        mat = mesh.materials[material_id]
        texture_node = get_active_material_texture_slot(mat)
        if texture_node:
            x *= texture_node.texture_mapping.scale[0]
            y *= texture_node.texture_mapping.scale[1]
            x += texture_node.texture_mapping.translation[0]
            y += texture_node.texture_mapping.translation[1]
        return (x, y)


class NodeProperties:
    def __init__(self, node):
        ac = node.assettoCorsa
        self.name = node.name
        self.lodIn = ac.lodIn
        self.lodOut = ac.lodOut
        self.layer = ac.layer
        self.castShadows = ac.castShadows
        self.visible = ac.visible
        self.transparent = ac.transparent
        self.renderable = ac.renderable


NODE_SETTINGS = (

)

class node_settings:
    def __init__(self, settings, node_settings_key):
        self._settings = settings
        self._node_settings_key = node_settings_key
        self._node_name_matches = self._convert_to_matches_list(node_settings_key)

    def apply_settings_to_node(self, node):
        if not self._does_node_name_match(node.name):
            return
        lodIn = self.getNodeLodIn()
        if lodIn is not None:
            node.lodIn = lodIn
        lodOut = self.getNodeLodOut()
        if lodOut is not None:
            node.lodOut = lodOut
        layer = self.getNodeLayer()
        if layer is not None:
            node.layer = layer
        castShadows = self.getNodeCastShadows()
        if castShadows is not None:
            node.castShadows = castShadows
        visible = self.getNodeIsVisible()
        if visible is not None:
            node.visible = visible
        transparent = self.getNodeIsTransparent()
        if transparent is not None:
            node.transparent = transparent
        renderable = self.getNodeIsRenderable()
        if renderable is not None:
            node.renderable = renderable

    def _does_node_name_match(self, node_name):
        for regex in self._node_name_matches:
            if regex.match(node_name):
                return True
        return False

    def _convert_to_matches_list(self, key):
        matches = []
        for subkey in key.split("|"):
            matches.append(re.compile(f"^{self._escape_match_key(subkey)}$", re.IGNORECASE))
        return matches

    def _escape_match_key(self, key):
        wildcardReplacement="__WILDCARD__"
        key=key.replace("*",wildcardReplacement)
        key=re.escape(key)
        key=key.replace(wildcardReplacement, ".*")
        return key

    def getNodeLodIn(self):
        if "lodIn" in self._settings[NODES][self._node_settings_key]:
            return self._settings[NODES][self._node_settings_key]["lodIn"]
        return None

    def getNodeLodOut(self):
        if "lodOut" in self._settings[NODES][self._node_settings_key]:
            return self._settings[NODES][self._node_settings_key]["lodOut"]
        return None

    def getNodeLayer(self):
        if "layer" in self._settings[NODES][self._node_settings_key]:
            return self._settings[NODES][self._node_settings_key]["layer"]
        return None

    def getNodeCastShadows(self):
        if "castShadows" in self._settings[NODES][self._node_settings_key]:
            return self._settings[NODES][self._node_settings_key]["castShadows"]
        return None

    def getNodeIsVisible(self):
        if "isVisible" in self._settings[NODES][self._node_settings_key]:
            return self._settings[NODES][self._node_settings_key]["isVisible"]
        return None

    def getNodeIsTransparent(self):
        if "isTransparent" in self._settings[NODES][self._node_settings_key]:
            return self._settings[NODES][self._node_settings_key]["isTransparent"]
        return None

    def getNodeIsRenderable(self):
        if "isRenderable" in self._settings[NODES][self._node_settings_key]:
            return self._settings[NODES][self._node_settings_key]["isRenderable"]
        return None


class UvVertex:
    def __init__(self, co, normal, uv, tangent):
        self.co = co
        self.normal = normal
        self.uv = uv
        self.tangent = tangent
        self.hash = None

    def __hash__(self):
        if not self.hash:
            self.hash = hash(hash(self.co[0]) ^
                        hash(self.co[1]) ^
                        hash(self.co[2]) ^
                        hash(self.normal[0]) ^
                        hash(self.normal[1]) ^
                        hash(self.normal[2]) ^
                        hash(self.uv[0]) ^
                        hash(self.uv[1]) ^
                        hash(self.tangent[0]) ^
                        hash(self.tangent[1]) ^
                        hash(self.tangent[2]))
        return self.hash

    def __eq__(self, other):
        if self.co[0] != other.co[0] or self.co[1] != other.co[1] or self.co[2] != other.co[2]:
            return False
        if self.normal[0] != other.normal[0] or self.normal[1] != other.normal[1] or self.normal[2] != other.normal[2]:
            return False
        if self.uv[0] != other.uv[0] or self.uv[1] != other.uv[1]:
            return False
        if self.tangent[0] != other.tangent[0] or self.tangent[1] != other.tangent[1] or self.tangent[2] != other.tangent[2]:
            return False
        return True


class Mesh:
    def __init__(self, material_id, vertices, indices):
        self.material_id = material_id
        self.vertices = vertices
        self.indices = indices
