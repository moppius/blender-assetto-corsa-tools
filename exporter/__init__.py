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


import os
import bpy
from bpy_extras.io_utils import ExportHelper
from .texture_writer import TextureWriter
from .material_writer import MaterialsWriter
from .node_writer import NodeWriter
from . import utils
from ..utils.constants import KN5_HEADER_BYTES


class ExportKN5(bpy.types.Operator, ExportHelper):
    bl_idname      = "exporter.kn5"
    bl_label       = "Export KN5"
    bl_description = "Export KN5"

    filename_ext = ".kn5"
    fileVersion  = 5

    def execute(self, context):
        warnings = []
        try:
            output_file = open(self.filepath,"wb")
            try:
                settings = kn5Helper.readSettings(self.filepath)
                self._write_header(output_file)
                self._write_content(output_file, context, settings, warnings)
                bpy.ops.kn5.report_message(
                    'INVOKE_DEFAULT',
                    isError=False,
                    title = "Exported successfully",
                    message = os.linesep.join(warnings)
                )
            finally:
                if not output_file is None:
                    output_file.close()
        except:
            error = traceback.format_exc()
            try:
                os.remove(self.filepath) # Remove output file so that nobody has the chance
                                         # to crash the engine with a broken file
            except:
                pass
            warnings.append(error)
            bpy.ops.kn5.report_message(
                'INVOKE_DEFAULT',
                isError=True,
                title = "Export failed",
                message = os.linesep.join(warnings)
            )
        return {'FINISHED'}

    def _write_header(self, output_file):
        output_file.write(KN5_HEADER_BYTES)
        kn5Helper.writeUInt(output_file, self.fileVersion)

    def _write_content(self, output_file, context, settings, warnings):
        texture_writer = TextureWriter(output_file, context, warnings)
        texture_writer.write()
        material_writer = MaterialsWriter(output_file, context, settings, warnings)
        material_writer.write()
        node_writer = NodeWriter(output_file, context, settings, warnings, material_writer)
        node_writer.write()


def menu_func(self, context):
    self.layout.operator(ExportKN5.bl_idname, text="Assetto Corsa (.kn5)")


REGISTER_CLASSES = (
    ExportKN5,
)


def register():
    for cls in REGISTER_CLASSES:
        bpy.utils.register_class(cls)
    bpy.types.TOPBAR_MT_file_export.append(menu_func)


def unregister():
    bpy.types.TOPBAR_MT_file_export.remove(menu_func)
    for cls in reversed(REGISTER_CLASSES):
        bpy.utils.unregister_class(cls)
