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


import struct
import bpy
import bmesh
from os import linesep, makedirs, path
from mathutils import Matrix, Vector
from .importer_utils import convert_matrix, convert_vector3
from ..utils.constants import ENCODING, KN5_HEADER_BYTES


TEXTURE_FOLDER = "texture"
NODE_TYPE_DUMMY = 1
NODE_TYPE_STATIC_MESH = 2
NODE_TYPE_ANIMATED_MESH = 3


class KN5Model():
    def __init__(self):
        self.folder = ""
        self.name = ""
        self.version = 5
        self.textures = []
        self.materials = []
        self.nodes = []


class KN5Texture():
    def __init__(self):
        self.type = 0
        self.name = ""
        self.filename = ""
        self.UVScaling = 1.0
        self.image_data = None


class KN5Material():
    def __init__(self):
        self.name = "Default"
        self.shader = ""
        self.ksAmbient = 0.6
        self.ksDiffuse = 0.6
        self.ksSpecular = 0.9
        self.ksSpecularEXP = 1.0
        self.diffuseMult = 1.0
        self.normalMult = 1.0
        self.useDetail = 0.0
        self.detailUVMultiplier = 1.0

        self.txDiffuse = None
        self.txNormal = None
        self.txDetail = None

        self.shaderProps = ""


class KN5Node():
    def __init__(self):
        self.type = NODE_TYPE_DUMMY
        self.name = "Default"
        self.parent_id = -1

        self.tmatrix = Matrix.Identity(4)
        self.hmatrix = Matrix.Identity(4)

        self.vertexCount = 0
        self.position = []
        self.normal = []
        self.uv = []
        self.tangent = []

        self.indices = []

        self.material_id = -1


class KN5Reader():
    def __init__(self, file, model: KN5Model, warnings: list):
        self.file = file
        self.model = model
        self.version = 0
        self.warnings = warnings

    def read(self):
        success = True
        try:
            self._read_header()
            self._read_textures()
            self._read_materials()
            self._read_nodes_recursive(self.model.nodes, -1)
        except:
            success = False
        return success

    def _read_header(self):
        if self.file.read(6) != KN5_HEADER_BYTES:
            self.warnings.append("Failed to find expected header!")
            return False

        self.version = self.read_uint()
        print(f"Successfully read header with version {self.version}!")
        if self.version > 5:
            unused_value = self.read_uint() # Not sure what this value is for

        return True

    def _read_textures(self):
        num_textures = self.read_int()
        print(f"Got {num_textures} textures")
        for _t in range(num_textures):
            texture = KN5Texture()
            texture.type = self.read_int()
            texture.name = self.read_string()
            texture_size = self.read_int()
            print(f"\ttype: {texture.type}, name: {texture.name}, size: {texture_size}")

            texture.filename = path.join(self.model.folder, TEXTURE_FOLDER, texture.name)
            if path.exists(texture.filename):
                print(f"\timage exists already: {texture.filename}")
                self.file.seek(texture_size, 1)
            else:
                print(f"\timage does not exist: {texture.filename}")
                texture.image_data = self.file.read(texture_size)

            self.model.textures.append(texture)

    def _read_materials(self):
        num_materials = self.read_int()
        print(f"Got {num_materials} materials")
        for _m in range(num_materials):
            material = KN5Material()

            material.name = self.read_string()
            material.shader = self.read_string()
            # TODO: Version handling?
            _alpha_blend_mode = self.read_byte()
            _alpha_tested = self.read_bool()
            _depth_mode = self.read_int()

            num_props = self.read_int()
            for _prop in range(num_props):
                prop_name = self.read_string()
                prop_float_value = self.read_float()
                _prop_vec2_value = self.read_vector2()
                _prop_vec3_value = self.read_vector3()
                _prop_vec4_value = self.read_vector4()
                material.shaderProps += f"{prop_name} = {prop_float_value}{linesep}"
                setattr(material, prop_name, prop_float_value)

            print(f"\tmaterial: {material.name} has {num_props} props")

            num_textures = self.read_int()
            for _t in range(num_textures):
                sample_name = self.read_string()
                _sample_slot = self.read_int()
                texture_name = self.read_string()
                material.shaderProps += f"{sample_name} = {texture_name}{linesep}"
                setattr(material, sample_name, texture_name)

            self.model.materials.append(material)

    def _read_nodes_recursive(self, nodes: list, parent_id: int):
        node = KN5Node()
        node.parent_id = parent_id
        node.type = self.read_int()
        node.name = self.read_string()
        num_children = self.read_int()
        is_active = self.read_bool()

        if node.type == NODE_TYPE_DUMMY:
            node.tmatrix = self.read_matrix()

        elif node.type == NODE_TYPE_STATIC_MESH:
            cast_shadows = self.read_bool()
            visible = self.read_bool()
            transparent = self.read_bool()

            node.vertexCount = self.read_uint()
            node.position = []
            node.normal = []
            node.uv = []

            for _vertex in range(node.vertexCount):
                node.position.append(convert_vector3(self.read_vector3()))
                node.normal.append(self.read_vector3())
                inverted_uv = self.read_vector2()
                node.uv.append((inverted_uv[0], -inverted_uv[1]))
                node.tangent.append(self.read_vector3())

            num_indices = self.read_uint()
            node.indices = [0 for _i in range(num_indices)]
            for i in range(num_indices):
                node.indices[i] = self.read_ushort()

            node.material_id = self.read_uint()
            layer = self.read_uint()
            lod_in = self.read_float()
            lod_out = self.read_float()
            # Bounding sphere
            sphere_center = self.read_vector3()
            sphere_radius = self.read_float()
            is_renderable = self.read_bool()


        elif node.type == NODE_TYPE_ANIMATED_MESH:
            '''
            byte bbyte = modelStream.ReadByte();
            byte cbyte = modelStream.ReadByte();
            byte dbyte = modelStream.ReadByte();

            int boneCount = modelStream.ReadInt32();
            for (int b = 0; b < boneCount; b++)
            {
                string boneName = ReadStr(modelStream, modelStream.ReadInt32());
                modelStream.BaseStream.Position += 64; //transformation matrix
            }

            node.vertexCount = modelStream.ReadInt32();
            node.position = new float[node.vertexCount * 3];
            node.normal = new float[node.vertexCount * 3];
            node.texture0 = new float[node.vertexCount * 2];

            for (int v = 0; v < node.vertexCount; v++)
            {
                node.position[v * 3] = modelStream.read_ushort();
                node.position[v * 3 + 1] = modelStream.read_ushort();
                node.position[v * 3 + 2] = modelStream.read_ushort();

                node.normal[v * 3] = modelStream.read_ushort();
                node.normal[v * 3 + 1] = modelStream.read_ushort();
                node.normal[v * 3 + 2] = modelStream.read_ushort();

                node.texture0[v * 2] = modelStream.read_ushort();
                node.texture0[v * 2 + 1] = 1 - modelStream.read_ushort();

                modelStream.BaseStream.Position += 44; //tangents & weights
            }

            int num_indices = modelStream.ReadInt32();
            node.indices = new ushort[num_indices];
            for i in range(num_indices):
                node.indices[i] = modelStream.ReadUInt16();

            node.material_id = modelStream.ReadInt32();
            modelStream.BaseStream.Position += 12;
            '''

        else:
            print(f"Unexpected node type {node.type}")

        if parent_id < 0:
            node.hmatrix = node.tmatrix
        else:
            node.hmatrix = node.tmatrix @ nodes[parent_id].hmatrix

        nodes.append(node)
        current_id = nodes.index(node)
        for _c in range(num_children):
            self._read_nodes_recursive(nodes, current_id)

    def read_string(self):
        str_len = self.read_int()
        binary_string = struct.unpack(f"{str_len}s", self.file.read(str_len))[0]
        return binary_string.decode(ENCODING)

    def read_uint(self):
        return struct.unpack("I", self.file.read(struct.calcsize("I")))[0]

    def read_int(self):
        return struct.unpack("i", self.file.read(struct.calcsize("i")))[0]

    def read_ushort(self):
        return struct.unpack("H", self.file.read(struct.calcsize("H")))[0]

    def read_byte(self):
        return struct.unpack("B", self.file.read(struct.calcsize("B")))[0]

    def read_bool(self):
        return struct.unpack("?", self.file.read(struct.calcsize("?")))[0]

    def read_float(self):
        return struct.unpack("f", self.file.read(struct.calcsize("f")))[0]

    def read_vector2(self):
        return struct.unpack("2f", self.file.read(struct.calcsize("2f")))

    def read_vector3(self):
        return Vector(struct.unpack("3f", self.file.read(struct.calcsize("3f"))))

    def read_vector4(self):
        return struct.unpack("4f", self.file.read(struct.calcsize("4f")))

    def read_matrix(self):
        matrix = Matrix()
        for row in range(4):
            for col in range(4):
                matrix[col][row] = self.read_float()
        return matrix


def create_blender_nodes(context, model, messages: list) -> bool:
    for texture in model.textures:
        if texture.image_data:
            # FIXME: Guess file extension if none is specified
            if not path.exists(texture.filename):
                parent_dir = path.dirname(texture.filename)
                if not path.exists(parent_dir):
                    makedirs(parent_dir)
                with open(texture.filename, 'wb') as texture_file:
                    texture_file.write(texture.image_data)
                    print(f"Created texture file: {texture.filename}")
            else:
                print(f"Warning: Texture file already exists: {texture.filename}")

    for material in model.materials:
        if not bpy.data.materials.get(material.name):
            new_material = bpy.data.materials.new(name=material.name)
            print(f"Created material: {new_material.name}")
        else:
            print("Found existing material '{material.name}', skipping creation")

    for node in model.nodes:
        if node.parent_id < 0:
            continue

        new_object = None

        if node.type == NODE_TYPE_DUMMY:
            new_object = bpy.data.objects.new(name=node.name, object_data=None)
            new_object.empty_display_type = 'ARROWS'

        elif node.type == NODE_TYPE_STATIC_MESH:
            mesh_data = bpy.data.meshes.new(name=f"{node.name}_Mesh")
            faces = []
            for i in range(0, len(node.indices), 3):
                faces.append([node.indices[i], node.indices[i + 1], node.indices[i + 2]])
            mesh_data.from_pydata(node.position, [], faces)

            bm = bmesh.new()
            bm.from_mesh(mesh_data)
            uv_layer = bm.loops.layers.uv.verify()
            for f in bm.faces:
                for l in f.loops:
                    luv = l[uv_layer]
                    luv.uv = node.uv[l.vert.index]
                    l.vert.normal = convert_vector3(node.normal[l.vert.index])
                f.smooth = True
            bm.to_mesh(mesh_data)
            bm.free()

            new_object = bpy.data.objects.new(name=node.name, object_data=mesh_data)
            material = bpy.data.materials.get(model.materials[node.material_id].name)
            if new_object.data.materials:
                new_object.data.materials[0] = material
            else:
                new_object.data.materials.append(material)

        else:
            print(f"Unexpected node type to create: {node.type}")

        if new_object is not None:
            new_object.matrix_world = convert_matrix(node.hmatrix)
            context.scene.collection.objects.link(new_object)

    return True
