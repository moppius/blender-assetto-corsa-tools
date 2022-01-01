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


bl_info = {
    "name":        "Assetto Corsa (.kn5)",
    "version":     (0, 2, 0),
    "author":      "Thomas Hagnhofer, Paul Greveson",
    "blender":     (3, 0, 0),
    "description": "Export to the Assetto Corsa KN5 format",
    "location":    "File Export menu, Object properties, Material properties",
    "support":     "COMMUNITY",
    "category":    "Import-Export",
    "doc_url":     "https://github.com/moppius/blender-assetto-corsa-tools#readme",
    "tracker_url": "https://github.com/moppius/blender-assetto-corsa-tools/issues",
}


if "bpy" in locals():
    import imp
    if "TextureWriter" in locals():
        imp.reload(TextureWriter)
    if "MaterialsWriter" in locals():
        imp.reload(MaterialsWriter)
    if "NodeWriter" in locals():
        imp.reload(NodeWriter)
    if "kn5Helper" in locals():
        imp.reload(kn5Helper)
    if "MaterialsUi" in locals():
        imp.reload(MaterialsUi)
    if "TexturesUi" in locals():
        imp.reload(TexturesUi)
    if "NodesUi" in locals():
        imp.reload(NodesUi)


import os
import struct
import sys
import traceback
import bpy
from bpy.props import *
from bpy_extras.io_utils import ExportHelper
from . import (
    kn5Helper,
    TextureWriter,
    MaterialsWriter,
    NodeWriter,
    MaterialsUi,
    TexturesUi,
    NodesUi,
)


class ReportOperator(bpy.types.Operator):
    bl_idname = "kn5.report_message"
    bl_label = "Export report"

    isError: BoolProperty()
    title: StringProperty()
    message: StringProperty()

    def execute(self, context):
        if self.isError:
            self.report({'WARNING'}, self.message)
        else:
            self.report({'INFO'}, self.message)
        return {'FINISHED'}

    def invoke(self, context, event):
        self.execute(context)
        wm = context.window_manager
        return wm.invoke_popup(self, width=600)

    def draw(self, context):
        if self.isError:
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


class ExportKN5(bpy.types.Operator, ExportHelper):
    fileVersion = 5
    bl_idname       = "exporter.kn5"
    bl_label        = "Export KN5"
    bl_description = "Export KN5"

    filename_ext    = ".kn5"

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
        textureWriter = TextureWriter.TextureWriter(file, context, warnings)
        textureWriter.write()
        materialsWriter = MaterialsWriter.MaterialsWriter(file, context, settings, warnings)
        materialsWriter.write()
        nodeWriter = NodeWriter.NodeWriter(file, context, settings, warnings, materialsWriter)
        nodeWriter.write()


def menu_func(self, context):
    self.layout.operator(ExportKN5.bl_idname, text="Assetto Corsa (.kn5)")


classes = (
    ReportOperator,
    CopyClipboardButtonOperator,
    ExportKN5,
)


def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)
    bpy.types.TOPBAR_MT_file_export.append(menu_func)
    MaterialsUi.register()
    TexturesUi.register()
    NodesUi.register()


def unregister():
    NodesUi.unregister()
    TexturesUi.unregister()
    MaterialsUi.unregister()
    bpy.types.TOPBAR_MT_file_export.remove(menu_func)
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)


if __name__ == "__main__":
    register()
