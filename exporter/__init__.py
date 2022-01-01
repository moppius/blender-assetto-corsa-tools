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
from bpy_extras.io_utils import ExportHelper
from .texture_writer import TextureWriter
from .material_writer import MaterialsWriter
from .node_writer import NodeWriter
from . import utils


class ExportKN5(bpy.types.Operator, ExportHelper):
    bl_idname      = "exporter.kn5"
    bl_label       = "Export KN5"
    bl_description = "Export KN5"

    filename_ext = ".kn5"
    fileVersion  = 5

    def execute(self, context):
        warnings = []
        try:
            outputFile = open(self.filepath,"wb")
            try:
                settings = kn5Helper.readSettings(self.filepath)
                self.writeHeader(outputFile)
                self.writeContent(outputFile, context, settings, warnings)
                bpy.ops.kn5.report_message('INVOKE_DEFAULT', isError=False, title = "Export successfully",
                                            message = os.linesep.join(warnings))
            finally:
                if not outputFile is None:
                    outputFile.close()
        except:
            error=traceback.format_exc()
            try:
                os.remove(self.filepath) #Remove output file so that nobody has the chance
                                         #to crash the engine with a broken file
            except:
                pass
            warnings.append(error)
            bpy.ops.kn5.report_message('INVOKE_DEFAULT', isError=True, title = "Export failed",
                                       message = os.linesep.join(warnings))
        return {'FINISHED'}

    def writeHeader(self, file):
        file.write(b"sc6969")
        kn5Helper.writeUInt(file, self.fileVersion)

    def writeContent(self, file, context, settings, warnings):
        textureWriter = TextureWriter(file, context, warnings)
        textureWriter.write()
        materialsWriter = MaterialsWriter(file, context, settings, warnings)
        materialsWriter.write()
        nodeWriter = NodeWriter(file, context, settings, warnings, materialsWriter)
        nodeWriter.write()


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
