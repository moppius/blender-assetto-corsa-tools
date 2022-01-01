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
import tempfile
from . import utils


class TextureWriter():
    def __init__(self, file, context, warnings):
        self.availableTextures={}
        self.texturePositions={}
        self.file = file
        self.warnings = warnings
        self.context = context
        self.fillAvailableImageTextures()

    def write(self):
        kn5Helper.writeInt(self.file,len(self.availableTextures))
        for textureName, position in sorted(self.texturePositions.items(), key=lambda k: k[1]):
            self.writeTexture(self.availableTextures[textureName])

    def writeTexture(self, texture):
        kn5Helper.writeInt(self.file, 1) #IsActive
        kn5Helper.writeString(self.file, texture.name)
        imageData=self.getImageDataFromTexture(texture)
        kn5Helper.writeBlob(self.file, imageData)

    def fillAvailableImageTextures(self):
        self.availableTextures={}
        self.texturePositions={}
        position = 0
        for texture in self.context.blend_data.textures:
            if not texture.name.startswith("__") and texture.type == "IMAGE":
                if texture.users == 0:
                    self.warnings.append("Ignoring unused texture '%s'" % texture.name)
                elif texture.image is None:
                    self.warnings.append("Ignoring texture without image '%s'" % texture.name)
                elif len(texture.image.pixels) == 0:
                    self.warnings.append("Ignoring texture without image data '%s'" % texture.name)
                else:
                    self.availableTextures[texture.name] = texture
                    self.texturePositions[texture.name] = position
                    position+=1

    def getImageDataFromTexture(self, texture):
        image=texture.image
        imageCopy=image.copy()
        try:
            if imageCopy.file_format in ("PNG", "DDS", ""):
                if imageCopy.packed_file is None:
                    imageCopy.pack(False)
                imageData = imageCopy.packed_file.data
                magicBytes = imageData[:3]
                if imageCopy.file_format != "" or magicBytes == b"DDS":
                    return imageData
            return self.convertImageToPng(imageCopy)
        finally:
            self.context.blend_data.images.remove(imageCopy)

    def convertImageToPng(self, image):
        if image.packed_file is not None:
            image.unpack("WRITE_LOCAL")
        image.pack(True)
        return image.packed_file.data
