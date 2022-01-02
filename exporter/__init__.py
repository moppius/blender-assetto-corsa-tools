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


import traceback
import os
import bpy
from bpy.props import BoolProperty, StringProperty
from bpy_extras.io_utils import ExportHelper
from .kn5_writer import KN5Writer
from .texture_writer import TextureWriter
from .material_writer import MaterialsWriter
from .node_writer import NodeWriter
from ..utils import readSettings
from ..utils.constants import KN5_HEADER_BYTES


class ReportOperator(bpy.types.Operator):
    bl_idname = "kn5.report_message"
    bl_label = "Export report"

    is_error: BoolProperty()
    title: StringProperty()
    message: StringProperty()

    def execute(self, context):
        if self.is_error:
            self.report({'WARNING'}, self.message)
        else:
            self.report({'INFO'}, self.message)
        return {'FINISHED'}

    def invoke(self, context, event):
        self.execute(context)
        wm = context.window_manager
        return wm.invoke_popup(self, width=600)

    def draw(self, context):
        if self.is_error:
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


class KN5FileWriter(KN5Writer):
    def __init__(self, file, context, settings, warnings):
        super().__init__(file)

        self.context = context
        self.settings = settings
        self.warnings = warnings

        self.file_version = 5

    def write(self):
        self._write_header()
        self._write_content()

    def _write_header(self):
        self.file.write(KN5_HEADER_BYTES)
        self.write_uint(self.file_version)

    def _write_content(self):
        texture_writer = TextureWriter(self.file, self.context, self.warnings)
        texture_writer.write()
        material_writer = MaterialsWriter(self.file, self.context, self.settings, self.warnings)
        material_writer.write()
        node_writer = NodeWriter(self.file, self.context, self.settings, self.warnings, material_writer)
        node_writer.write()


class ExportKN5(bpy.types.Operator, ExportHelper):
    bl_idname      = "exporter.kn5"
    bl_label       = "Export KN5"
    bl_description = "Export KN5"

    filename_ext = ".kn5"

    def execute(self, context):
        warnings = []
        try:
            output_file = open(self.filepath,"wb")
            try:
                settings = readSettings(self.filepath)
                kn5_writer = KN5FileWriter(output_file, context, settings, warnings)
                kn5_writer.write()
                bpy.ops.kn5.report_message(
                    'INVOKE_DEFAULT',
                    is_error=False,
                    title="Exported successfully",
                    message=os.linesep.join(warnings)
                )
            finally:
                if not output_file is None:
                    output_file.close()
        except:
            error = traceback.format_exc()
            try:
                # Remove output file so we can't crash the engine with a broken file
                os.remove(self.filepath)
            except:
                pass
            warnings.append(error)
            bpy.ops.kn5.report_message(
                'INVOKE_DEFAULT',
                is_error=True,
                title="Export failed",
                message=os.linesep.join(warnings)
            )
        return {'FINISHED'}


def menu_func(self, context):
    self.layout.operator(ExportKN5.bl_idname, text="Assetto Corsa (.kn5)")


REGISTER_CLASSES = (
    ReportOperator,
    CopyClipboardButtonOperator,
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
