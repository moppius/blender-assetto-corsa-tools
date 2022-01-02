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


import mathutils
import math
import os
import re
from .exporter_utils import (
    convert_matrix,
    convertVector3,
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
    def __init__(self, file, context, settings, warnings, materialsWriter):
        super().__init__(file)

        self.nodeSettings = []
        self.context = context
        self.settings = settings
        self.warnings = warnings
        self.materialsWriter = materialsWriter
        self.scene = self.context.blend_data.scenes[0]
        self.initAcObjects()
        self.initNodeSettings()

    def initNodeSettings(self):
        self.nodeSettings = []
        if NODES in self.settings:
            for nodeKey in self.settings[NODES]:
                self.nodeSettings.append(NodeSettings(self.settings, nodeKey))

    def initAcObjects(self):
        self.acObjects=[]
        for o in ASSETTO_CORSA_OBJECTS:
            self.acObjects.append(re.compile(f"^{o}$"))

    def is_ac_object(self, name):
        for regex in self.acObjects:
            if regex.match(name):
                return True
        return False

    def write(self):
        self.writeBaseNode(None, "BlenderFile")
        for o in sorted(self.context.blend_data.objects, key=lambda k: len(k.children)):
            if not o.parent:
                self.writeObject(o)

    def writeObject(self, obj):
        if not obj.name.startswith("__"):
            if obj.type == "MESH":
                if len(obj.children) != 0:
                    raise Exception(f"A mesh cannot contain children ('{obj.name}')")
                self.writeMeshNode(obj)
            else:
                self.writeBaseNode(obj, obj.name)
            for child in obj.children:
                self.writeObject(child)

    def any_child_is_mesh(self, obj):
        for child in obj.children:
            if child.type in ["MESH", "CURVE"] or self.any_child_is_mesh(child):
                return True
        return False

    def writeBaseNode(self, obj, nodeName):
        nodeData={}
        matrix = None
        childCount = 0
        if not obj:
            matrix = mathutils.Matrix()
            for o in self.context.blend_data.objects:
                if not o.parent and not o.name.startswith("__"):
                    childCount += 1
        else:
            if not self.is_ac_object(obj.name) and not self.any_child_is_mesh(obj):
                self.warnings.append(f"Unknown logical object '{obj.name}' might prevent other objects from loading.{os.linesep}\tRename it to '__{obj.name}' if you do not want to export it.")
            matrix = convert_matrix(obj.matrix_local)
            for child in obj.children:
                if not child.name.startswith("__"):
                    childCount += 1

        nodeData["name"] = nodeName
        nodeData["childCount"] = childCount
        nodeData["active"] = True
        nodeData["transform"] = matrix
        self.writeBaseNodeData(nodeData)

    def writeBaseNodeData(self, nodeData):
        self.write_node_class("Node")
        self.write_string(nodeData["name"])
        self.write_uint(nodeData["childCount"])
        self.write_bool(nodeData["active"])
        self.write_matrix(nodeData["transform"])

    def writeMeshNode(self, obj):
        divided_meshes = self._split_object_by_materials(obj)
        divided_meshes = self._split_meshes_for_vertex_limit(divided_meshes)
        if obj.parent or len(divided_meshes) > 1:
            nodeData = {}
            nodeData["name"] = obj.name
            nodeData["childCount"] = len(divided_meshes)
            nodeData["active"] = True
            transformMatrix = mathutils.Matrix()
            if obj.parent:
                transformMatrix = convert_matrix(obj.parent.matrix_world.inverted())
            nodeData["transform"] = transformMatrix
            self.writeBaseNodeData(nodeData)
        nodeProperties = NodeProperties(obj)
        for nodeSetting in self.nodeSettings:
            nodeSetting.apply_settings_to_node(nodeProperties)
        for mesh in divided_meshes:
            self.writeMesh(obj, mesh, nodeProperties)

    def write_node_class(self, nodeClass):
        self.write_uint(NodeClass[nodeClass])

    def writeMesh(self, obj, mesh, nodeProperties):
        self.write_node_class("Mesh")
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
        self.writeBoundingSphere(mesh.vertices)
        self.write_bool(nodeProperties.renderable) #isRenderable

    def writeBoundingSphere(self, vertices):
        maxX = -999999999
        maxY = -999999999
        maxZ = -999999999
        minX = 999999999
        minY = 999999999
        minZ = 999999999
        for v in vertices:
            co = v.co
            if co[0] > maxX:
               maxX = co[0]
            if co[0] < minX:
               minX = co[0]
            if co[1] > maxY:
               maxY = co[1]
            if co[1] < minY:
               minY = co[1]
            if co[2] > maxZ:
               maxZ = co[2]
            if co[2] < minZ:
               minZ = co[2]

        sphereCenter = [
            minX + (maxX - minX) / 2,
            minY + (maxY - minY) / 2,
            minZ + (maxZ - minZ) / 2
        ]
        sphereRadius = max((maxX - minX) / 2, (maxY - minY) / 2, (maxZ - minZ) / 2) * 2
        self.write_vector3(sphereCenter)
        self.write_float(sphereRadius)

    def _split_object_by_materials(self, obj):
        meshes = []
        mesh_copy = obj.to_mesh()
        try:
            uv_layer = mesh_copy.uv_layers.active
            mesh_vertices = mesh_copy.vertices[:]
            mesh_copy.calc_loop_triangles()
            mesh_faces = mesh_copy.loop_triangles[:]
            matrix = obj.matrix_world

            if not mesh_copy.materials:
                raise Exception(f"Object '{obj.name}' has no material assigned")

            used_materials=set([face.material_index for face in mesh_faces])
            for material_index in used_materials:
                if not mesh_copy.materials[material_index]:
                    raise Exception(f"Material slot {material_index} for object '{obj.name}' has no material assigned")
                material_name = mesh_copy.materials[material_index].name
                if material_name.startswith("__") :
                    raise Exception(f"Material '{material_name}' is ignored but is used by object '{obj.name}'")

                vertices = {}
                indices = []
                for face in mesh_faces:
                    if material_index != face.material_index:
                        continue
                    vertexIndexForFace = 0
                    face_indices = []
                    for v_index in face.vertices:
                        v = mesh_vertices[v_index]
                        local_position = matrix @ v.co
                        convertedPosition = convertVector3(local_position)
                        convertedNormal = convertVector3(v.normal)
                        uv = (0, 0)
                        if uv_layer:
                            uv = uv_layer.data[face.index].uv
                            uv = (uv[0], -uv[1])
                        else:
                            uv = self._calculate_uvs(obj, mesh_copy, material_index, local_position)
                        tangent = (1.0, 0.0, 0.0)
                        vertex = UvVertex(convertedPosition, convertedNormal, uv, tangent)
                        if not vertex in vertices:
                            newIndex = len(vertices)
                            vertices[vertex] = newIndex
                        face_indices.append(vertices[vertex])
                        vertexIndexForFace += 1
                    indices.extend((face_indices[1], face_indices[2], face_indices[0]))
                    if len(face_indices) == 4:
                        indices.extend((face_indices[2], face_indices[3], face_indices[0]))
                vertices = [v for v, index in sorted(vertices.items(), key=lambda k: k[1])]
                material_id = self.materialsWriter.material_positions[material_name]
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

class NodeSettings:
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

    def _does_node_name_match(self, nodeName):
        for regex in self._node_name_matches:
            if regex.match(nodeName):
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
