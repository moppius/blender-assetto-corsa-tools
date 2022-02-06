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
from .kn5_reader import create_blender_nodes, KN5Model, KN5Reader


def import_kn5_file(file_name: str, model: KN5Model, messages: list) -> bool:
    model.folder = path.dirname(file_name)
    model.name = file_name
    print(f"folder: {model.folder}, name = {model.name}")
    with open(file_name, "rb") as input_file:
        reader = KN5Reader(input_file, model, messages)
        success = reader.read()
    if not success:
        print("FAIL READ")
    return success


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
                    is_error=True,
                    title="Import failed",
                    message=linesep.join(messages)
                )
        except:
            error = traceback.format_exc()
            messages.append(error)
            bpy.ops.kn5.report_message(
                'INVOKE_DEFAULT',
                is_error=True,
                title="Import failed",
                message=linesep.join(messages)
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
