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

import numbers
import os
import re
from . import kn5Helper

BlendMode = {
    "Opaque" : 0,
    "AlphaBlend" : 1,
    "AlphaToCoverage" : 2
}

DepthMode = {
    "DepthNormal" : 0,
    "DepthNoWrite" : 1,
    "DepthOff" : 2
}


class MaterialsWriter():
    def __init__(self, file, context, settings, warnings):
        self.availableMaterials = {}
        self.materialPositions = {}
        self.materialSettings = []
        self.file = file
        self.context = context
        self.settings = settings
        self.warnings = warnings
        self.fillAvailableMaterials()

    def write(self):
        kn5Helper.writeInt(self.file,len(self.availableMaterials))
        for materialName, position in sorted(self.materialPositions.items(), key=lambda k: k[1]):
            material=self.availableMaterials[materialName]
            self.writeMaterial(material)

    def writeMaterial(self, material):
        kn5Helper.writeString(self.file, material.name)
        kn5Helper.writeString(self.file, material.shaderName)
        kn5Helper.writeByte(self.file, material.alphaBlendMode)
        kn5Helper.writeBool(self.file, material.alphaTested)
        kn5Helper.writeInt(self.file, material.depthMode)
        kn5Helper.writeUInt(self.file, len(material.shaderProperties))
        for propertyName in material.shaderProperties:
            self.writeMaterialProperty(material.shaderProperties[propertyName])
        kn5Helper.writeUInt(self.file, len(material.textureMapping))
        textureSlot=0
        for mappingName in material.textureMapping:
            kn5Helper.writeString(self.file, mappingName)
            kn5Helper.writeUInt(self.file, textureSlot)
            kn5Helper.writeString(self.file, material.textureMapping[mappingName])
            textureSlot+=1

    def writeMaterialProperty(self, property):
        kn5Helper.writeString(self.file, property.name)
        kn5Helper.writeFloat(self.file, property.valueA)
        kn5Helper.writeVector2(self.file, property.valueB)
        kn5Helper.writeVector3(self.file, property.valueC)
        kn5Helper.writeVector4(self.file, property.valueD)

    def fillAvailableMaterials(self):
        self.availableMaterials={}
        self.materialPositions={}
        self.materialSettings=[]
        if "materials" in self.settings:
            for materialKey in self.settings["materials"]:
                self.materialSettings.append(MaterialSettings(self.settings, self.warnings, materialKey))
        position = 0
        for material in self.context.blend_data.materials:
            if material.users == 0:
                self.warnings.append("Ignoring unused material '%s'" % material.name)
            elif not material.name.startswith("__"):
                if kn5Helper.getActiveMaterialTextureSlot(material) is None:
                    self.warnings.append("No active texture for material '%s' found.%s\tUsing default UV scaling for objects without UV maps."% (material.name, os.linesep))
                materialProperties=MaterialProperties(material)
                for setting in self.materialSettings:
                    setting.applySettingsToMaterial(materialProperties)
                self.availableMaterials[material.name] = materialProperties
                self.materialPositions[material.name] = position
                position+=1

class ShaderProperty:
    def __init__(self, name):
        self.name=name
        self.valueA=0.0
        self.valueB=(0.0, 0.0)
        self.valueC=(0.0, 0.0, 0.0)
        self.valueD=(0.0, 0.0, 0.0, 0.0)
    def fill(self, property):
        self.valueA=property.valueA
        self.valueB=property.valueB
        self.valueC=property.valueC
        self.valueD=property.valueD

class MaterialProperties:
    def __init__(self, material):
        self.name=material.name
        ac=material.assettoCorsa
        self.shaderName=ac.shaderName
        self.alphaBlendMode = int(ac.alphaBlendMode)
        self.alphaTested = ac.alphaTested
        self.depthMode = int(ac.depthMode)
        self.shaderProperties=self.copyShaderProperties(material)
        self.textureMapping=self.generateTextureMapping(material)

    def copyShaderProperties(self, material):
        ac=material.assettoCorsa
        properties={}
        for property in ac.shaderProperties:
            newProperty=ShaderProperty(property.name)
            newProperty.fill(property)
            properties[property.name]=newProperty
        #Add a default ksDiffuse value for all objects without any properties set
        if len(properties) == 0 and ac.shaderName == "ksPerPixel":
            newProperty=ShaderProperty("ksDiffuse")
            newProperty.valueA=0.4
            properties[newProperty.name]=newProperty
            newProperty=ShaderProperty("ksAmbient")
            newProperty.valueA=0.4
            properties[newProperty.name]=newProperty
        return properties

    def generateTextureMapping(self, material):
        mapping={}
        for textureIndex in range(0, len(material.texture_slots)):
            if material.texture_slots[textureIndex] is not None and material.texture_slots[textureIndex].use:
                textureSlot=material.texture_slots[textureIndex]
                texture=textureSlot.texture
                if not texture.name.startswith("__"):
                    shaderInput=texture.assettoCorsa.shaderInputName
                    mapping[shaderInput]=texture.name
        return mapping

class MaterialSettings:
    def __init__(self, settings, warnings, materialSettingsKey):
        self.settings = settings
        self.warnings = warnings
        self.materialSettingsKey=materialSettingsKey
        self.materialNameMatches=self.convertToMatchesList(materialSettingsKey)

    def applySettingsToMaterial(self, material):
        if not self.doesMaterialNameMatch(material.name):
            return
        shaderName=self.getMaterialShader()
        if shaderName is not None:
            material.shaderName=shaderName
        alphaBlendMode = self.getMaterialBlendMode()
        if alphaBlendMode is not None:
            material.alphaBlendMode=alphaBlendMode
        alphaTested = self.getMaterialAlphaTested()
        if alphaTested is not None:
            material.alphaTested=self.getMaterialAlphaTested()
        depthMode = self.getMaterialDepthMode()
        if depthMode is not None:
            material.depthMode=self.getMaterialDepthMode()
        propertyNames=self.getMaterialPropertyNames()
        if len(propertyNames) > 0:
            material.shaderProperties.clear()
        for propertyName in propertyNames:
            shaderProperty=None
            if propertyName in material.shaderProperties:
                shaderProperty=material.shaderProperties[propertyName]
            else:
                shaderProperty=ShaderProperty(propertyName)
                material.shaderProperties[propertyName]=shaderProperty
            valueA=self.getMaterialPropertyValueA(propertyName)
            if valueA is not None:
                shaderProperty.valueA=valueA
            valueB=self.getMaterialPropertyValueB(propertyName)
            if valueB is not None:
                shaderProperty.valueB=valueB
            valueC=self.getMaterialPropertyValueC(propertyName)
            if valueC is not None:
                shaderProperty.valueC=valueC
            valueD=self.getMaterialPropertyValueD(propertyName)
            if valueD is not None:
                shaderProperty.valueD=valueD
        textureMappingNames=self.getMaterialTextureMappingNames()
        if len(textureMappingNames) > 0:
            material.textureMapping.clear()
        for textureMappingName in textureMappingNames:
            textureName=self.getMaterialTextureMappingTextureName(textureMappingName)
            if textureName is None:
                self.warnings.append("Ignoring texture mapping '%s' for material '%s' without texture name" % (textureName, material.name))
            else:
                material.textureMapping[textureMappingName]=textureName

    def doesMaterialNameMatch(self, materialName):
        for regex in self.materialNameMatches:
            if regex.match(materialName) is not None:
                return True
        return False

    def convertToMatchesList(self, key):
        matches=[]
        for subkey in key.split("|"):
            matches.append(re.compile("^" + self.escapeMatchKey(subkey) + "$", re.IGNORECASE))
        return matches

    def escapeMatchKey(self, key):
        wildcardReplacement="__WILDCARD__"
        key=key.replace("*",wildcardReplacement)
        key=re.escape(key)
        key=key.replace(wildcardReplacement, ".*")
        return key

    def getMaterialShader(self):
        if "shaderName" in self.settings["materials"][self.materialSettingsKey]:
            return self.settings["materials"][self.materialSettingsKey]["shaderName"]
        return None

    def getMaterialBlendMode(self):
        if "alphaBlendMode" in self.settings["materials"][self.materialSettingsKey]:
            return BlendMode[self.settings["materials"][self.materialSettingsKey]["alphaBlendMode"]]
        return None

    def getMaterialDepthMode(self):
        if "depthMode" in self.settings["materials"][self.materialSettingsKey]:
            return DepthMode[self.settings["materials"][self.materialSettingsKey]["depthMode"]]
        return None

    def getMaterialAlphaTested(self):
        if "alphaTested" in self.settings["materials"][self.materialSettingsKey]:
            return self.settings["materials"][self.materialSettingsKey]["alphaTested"]
        return None

    def getMaterialPropertyNames(self):
        if "properties" in self.settings["materials"][self.materialSettingsKey]:
            return self.settings["materials"][self.materialSettingsKey]["properties"]
        return []

    def getMaterialPropertyValue(self, propertyName, valueName):
        if valueName in self.settings["materials"][self.materialSettingsKey]["properties"][propertyName]:
            return self.settings["materials"][self.materialSettingsKey]["properties"][propertyName][valueName]
        return None

    def getMaterialTextureMappingNames(self):
        if "textures" in self.settings["materials"][self.materialSettingsKey]:
            return self.settings["materials"][self.materialSettingsKey]["textures"]
        return []

    def getMaterialTextureMappingTextureName(self, mappingName):
        if "textures" in self.settings["materials"][self.materialSettingsKey]:
            return self.settings["materials"][self.materialSettingsKey]["textures"][mappingName]["textureName"]
        return None

    def getMaterialPropertyValueA(self, propertyName):
        valueA = self.getMaterialPropertyValue(propertyName, "valueA")
        if valueA is None:
            return None
        if not isinstance(valueA, numbers.Number):
            raise Exception("valueA must be a float")
        return valueA

    def getMaterialPropertyValueB(self, propertyName):
        valueB = self.getMaterialPropertyValue(propertyName, "valueB")
        if valueB is None:
            return None
        if not self.isListOfNumbersValid(valueB, 2):
            raise Exception("valueB must be a list of two floats")
        return valueB

    def getMaterialPropertyValueC(self, propertyName):
        valueC = self.getMaterialPropertyValue(propertyName, "valueC")
        if valueC is None:
            return None
        if not self.isListOfNumbersValid(valueC, 3):
            raise Exception("valueC must be a list of three floats")
        return valueC

    def getMaterialPropertyValueD(self, propertyName):
        valueD = self.getMaterialPropertyValue(propertyName, "valueD")
        if valueD is None:
            return None
        if not self.isListOfNumbersValid(valueD, 4):
            raise Exception("valueD must be a list of four floats")
        return valueD

    def isListOfNumbersValid(self, list, count):
        if not (not hasattr(list, "strip") and (hasattr(list, "__getitem__") or hasattr(list, "__iter__"))):
            return False
        elif len(list) != count:
            return False
        return all([isinstance(x, numbers.Number) for x in list])