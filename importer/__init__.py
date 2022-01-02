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


import traceback
from os import linesep, makedirs, path
import bpy
from bpy_extras.io_utils import ImportHelper
from mathutils import Matrix, Vector
from . import importer_utils as utils


KN5_HEADER = b"sc6969"
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

        self.materialID = -1


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
            print(f"Created material: {material.name}")
        else:
            print("Found existing material '{material.name}', skipping creation")

    for node in model.nodes:
        if node.parent_id < 0:
            continue

        if node.type == NODE_TYPE_DUMMY:
            empty = bpy.data.objects.new(node.name, None)
            empty.empty_display_type = 'ARROWS'
            context.scene.collection.objects.link(empty)
            empty.matrix_world = node.hmatrix

        elif node.type == NODE_TYPE_STATIC_MESH:
            pass

        else:
            print(f"Unexpected node type to create: {node.type}")

    return True


def import_kn5_file(file_name: str, model: KN5Model(), messages: list) -> bool:
    model.folder = path.dirname(file_name)
    model.name = file_name
    print(f"folder: {model.folder}, name = {model.name}")
    with open(file_name, "rb") as input_file:
        # Header
        if input_file.read(6) != KN5_HEADER:
            messages.append("Failed to find expected header!")
            return False

        # Version
        model.version = utils.read_uint(input_file)
        print(f"Successfully read header with version {model.version}!")
        if model.version > 5:
            unused_value = utils.read_uint(input_file) # Not sure what this value is for

        # Textures
        num_textures = utils.read_int(input_file)
        print(f"Got {num_textures} textures")
        for t in range(num_textures):
            texture = KN5Texture()
            texture.type = utils.read_int(input_file)
            texture.name = utils.read_string(input_file)
            texture_size = utils.read_int(input_file)
            print(f"\ttype: {texture.type}, name: {texture.name}, size: {texture_size}")

            texture.filename = path.join(model.folder, TEXTURE_FOLDER, texture.name)
            if path.exists(texture.filename):
                print(f"\timage exists already: {texture.filename}")
                input_file.seek(texture_size, 1)
            else:
                print(f"\timage does not exist: {texture.filename}")
                texture.image_data = input_file.read(texture_size)

            model.textures.append(texture)

        # Materials
        num_materials = utils.read_int(input_file)
        print(f"Got {num_materials} materials")
        for m in range(num_materials):
            material = KN5Material()

            material.name = utils.read_string(input_file)
            material.shader = utils.read_string(input_file)
            # TODO: Version handling?
            alpha_blend_mode = utils.read_byte(input_file)
            alpha_tested = utils.read_bool(input_file)
            depth_mode = utils.read_int(input_file)

            num_props = utils.read_int(input_file)
            for p in range(num_props):
                prop_name = utils.read_string(input_file)
                prop_float_value = utils.read_float(input_file)
                prop_vec2_value = utils.read_vector2(input_file)
                prop_vec3_value = utils.read_vector3(input_file)
                prop_vec4_value = utils.read_vector4(input_file)
                material.shaderProps += f"{prop_name} = {prop_float_value}{linesep}"
                setattr(material, prop_name, prop_float_value)

            print(f"\tmaterial: {material.name} has {num_props} props")

            num_textures = utils.read_int(input_file)
            for t in range(num_textures):
                sample_name = utils.read_string(input_file)
                sample_slot = utils.read_int(input_file)
                texture_name = utils.read_string(input_file)
                material.shaderProps += f"{sample_name} = {texture_name}{linesep}"
                setattr(material, sample_name, texture_name)

            model.materials.append(material)

        _import_nodes_recursive(input_file, model.nodes, -1)

    return True


def _import_nodes_recursive(input_file, nodes: list, parent_id: int):
    node = KN5Node()
    node.parent_id = parent_id
    node.type = utils.read_int(input_file)
    node.name = utils.read_string(input_file)
    num_children = utils.read_int(input_file)
    is_active = utils.read_bool(input_file)

    if node.type == NODE_TYPE_DUMMY:
        node.tmatrix = utils.read_matrix(input_file)

    elif node.type == NODE_TYPE_STATIC_MESH:
        cast_shadows = utils.read_bool(input_file)
        visible = utils.read_bool(input_file)
        transparent = utils.read_bool(input_file)

        node.vertexCount = utils.read_uint(input_file)
        node.position = []
        node.normal = []
        node.uv = []

        for v in range(node.vertexCount):
            node.position.append(utils.read_vector3(input_file))
            node.normal.append(utils.read_vector3(input_file))
            node.uv.append(utils.read_vector2(input_file))
            node.tangent.append(utils.read_vector3(input_file))

        num_indices = utils.read_uint(input_file)
        node.indices = [0 for _ in range(num_indices)]
        for i in range(num_indices):
            node.indices[i] = utils.read_ushort(input_file)

        node.materialID = utils.read_uint(input_file)
        layer = utils.read_uint(input_file)
        lod_in = utils.read_float(input_file)
        lod_out = utils.read_float(input_file)
        # Bounding sphere
        sphere_center = utils.read_vector3(input_file)
        sphere_radius = utils.read_float(input_file)
        is_renderable = utils.read_bool(input_file)


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

        node.materialID = modelStream.ReadInt32();
        modelStream.BaseStream.Position += 12;
        '''

    else:
        print(f"Unexpected node type {node.type}")

    if parent_id < 0:
        node.hmatrix = node.tmatrix
    else:
        node.hmatrix =  node.tmatrix @ nodes[parent_id].hmatrix

    nodes.append(node)
    current_id = nodes.index(node)
    for c in range(num_children):
        _import_nodes_recursive(input_file, nodes, current_id)


class ImportKN5(bpy.types.Operator, ImportHelper):
    bl_idname = "importer.kn5"
    bl_label = "Import KN5"
    bl_description = "Import KN5"

    file_version = 6
    filename_ext = ".kn5"

    def execute(self, context):
        messages = []
        try:
            model = KN5Model()
            if (not import_kn5_file(self.filepath, model, messages)
                or not create_blender_nodes(context, model, messages)):
                bpy.ops.kn5.report_message(
                    'INVOKE_DEFAULT',
                    is_error = True,
                    title = "Import failed",
                    message = linesep.join(messages)
                )
        except:
            error = traceback.format_exc()
            messages.append(error)
            bpy.ops.kn5.report_message(
                'INVOKE_DEFAULT',
                is_error = True,
                title = "Import failed",
                message = linesep.join(messages)
            )
        return {'FINISHED'}


def menu_func(self, context):
    self.layout.operator(ImportKN5.bl_idname, text="Assetto Corsa (.kn5)")


REGISTER_CLASSES = (
    ImportKN5,
)


def register():
    for cls in REGISTER_CLASSES:
        bpy.utils.register_class(cls)
    bpy.types.TOPBAR_MT_file_import.append(menu_func)


def unregister():
    bpy.types.TOPBAR_MT_file_import.remove(menu_func)
    for cls in reversed(REGISTER_CLASSES):
        bpy.utils.unregister_class(cls)
