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
from .exporter_utils import (
    get_active_material_texture_slot,
    writeBool,
    writeByte,
    writeInt,
    writeString,
    writeUInt,
    writeFloat,
    writeVector2,
    writeVector3,
    writeVector4,
)


BlendMode = {
    "Opaque" : 0,
    "AlphaBlend" : 1,
    "AlphaToCoverage" : 2,
}

DepthMode = {
    "DepthNormal" : 0,
    "DepthNoWrite" : 1,
    "DepthOff" : 2,
}


MATERIALS = "materials"


class MaterialsWriter():
    def __init__(self, file, context, settings, warnings):
        self.available_materials = {}
        self.material_positions = {}
        self.material_settings = []
        self.file = file
        self.context = context
        self.settings = settings
        self.warnings = warnings
        self._fill_available_materials()

    def write(self):
        writeInt(self.file,len(self.available_materials))
        for materialName, position in sorted(self.material_positions.items(), key=lambda k: k[1]):
            material=self.available_materials[materialName]
            self.writeMaterial(material)

    def writeMaterial(self, material):
        writeString(self.file, material.name)
        writeString(self.file, material.shaderName)
        writeByte(self.file, material.alphaBlendMode)
        writeBool(self.file, material.alphaTested)
        writeInt(self.file, material.depthMode)
        writeUInt(self.file, len(material.shaderProperties))
        for propertyName in material.shaderProperties:
            self.writeMaterialProperty(material.shaderProperties[propertyName])
        writeUInt(self.file, len(material.textureMapping))
        textureSlot=0
        for mappingName in material.textureMapping:
            writeString(self.file, mappingName)
            writeUInt(self.file, textureSlot)
            writeString(self.file, material.textureMapping[mappingName])
            textureSlot+=1

    def writeMaterialProperty(self, property):
        writeString(self.file, property.name)
        writeFloat(self.file, property.valueA)
        writeVector2(self.file, property.valueB)
        writeVector3(self.file, property.valueC)
        writeVector4(self.file, property.valueD)

    def _fill_available_materials(self):
        self.available_materials = {}
        self.material_positions = {}
        self.material_settings = []
        if MATERIALS in self.settings:
            for materialKey in self.settings[MATERIALS]:
                self.material_settings.append(MaterialSettings(self.settings, self.warnings, materialKey))
        position = 0
        for material in self.context.blend_data.materials:
            if material.users == 0:
                self.warnings.append(f"Ignoring unused material '{material.name}'")
            elif not material.name.startswith("__"):
                if not get_active_material_texture_slot(material):
                    self.warnings.append(f"No active texture for material '{material.name}' found.{os.linesep}\tUsing default UV scaling for objects without UV maps.")
                materialProperties=MaterialProperties(material)
                for setting in self.material_settings:
                    setting.apply_settings_to_material(materialProperties)
                self.available_materials[material.name] = materialProperties
                self.material_positions[material.name] = position
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
        self.name = material.name
        ac = material.assettoCorsa
        self.shaderName = ac.shaderName
        self.alphaBlendMode = int(ac.alphaBlendMode)
        self.alphaTested = ac.alphaTested
        self.depthMode = int(ac.depthMode)
        self.shaderProperties = self.copy_shader_properties(material)
        self.textureMapping = self.generate_texture_mapping(material)

    def copy_shader_properties(self, material):
        ac = material.assettoCorsa
        properties = {}
        for shader_property in ac.shaderProperties:
            new_property = ShaderProperty(shader_property.name)
            new_property.fill(shader_property)
            properties[shader_property.name] = new_property
        # Add a default ksDiffuse value for all objects without any properties set
        if len(properties) == 0 and ac.shaderName == "ksPerPixel":
            new_property = ShaderProperty("ksDiffuse")
            new_property.valueA = 0.4
            properties[new_property.name] = new_property
            new_property = ShaderProperty("ksAmbient")
            new_property.valueA = 0.4
            properties[new_property.name] = new_property
        return properties

    def generate_texture_mapping(self, material):
        mapping = {}
        textures = []
        if material.node_tree:
            textures.extend([x for x in material.node_tree.nodes if x.type=='TEX_IMAGE'])
        print("TOLOYOYYOY")
        print(textures)
        for texture in textures:
            if texture.use:
                textureSlot = material.texture_slots[textureIndex]
                texture = textureSlot.texture
                if not texture.name.startswith("__"):
                    shaderInput = texture.assettoCorsa.shaderInputName
                    mapping[shaderInput] = texture.name
        return mapping

class MaterialSettings:
    def __init__(self, settings, warnings, material_settings_key):
        self.settings = settings
        self.warnings = warnings
        self.material_settings_key = material_settings_key
        self.material_name_matches = self.convert_to_matches_list(material_settings_key)

    def apply_settings_to_material(self, material):
        if not self.does_material_name_match(material.name):
            return
        shaderName = self.getMaterialShader()
        if shaderName:
            material.shaderName=shaderName

        alphaBlendMode = self.getMaterialBlendMode()
        if alphaBlendMode:
            material.alphaBlendMode = alphaBlendMode
        alphaTested = self.getMaterialAlphaTested()
        if alphaTested:
            material.alphaTested = self.getMaterialAlphaTested()
        depthMode = self.getMaterialDepthMode()
        if depthMode:
            material.depthMode = self.getMaterialDepthMode()

        property_names = self.getMaterialPropertyNames()
        if property_names:
            material.shaderProperties.clear()
        for propertyName in property_names:
            shaderProperty = None
            if propertyName in material.shaderProperties:
                shaderProperty = material.shaderProperties[propertyName]
            else:
                shaderProperty = ShaderProperty(propertyName)
                material.shaderProperties[propertyName]=shaderProperty
            valueA = self.getMaterialPropertyValueA(propertyName)
            if valueA:
                shaderProperty.valueA = valueA
            valueB = self.getMaterialPropertyValueB(propertyName)
            if valueB:
                shaderProperty.valueB = valueB
            valueC = self.getMaterialPropertyValueC(propertyName)
            if valueC:
                shaderProperty.valueC = valueC
            valueD = self.getMaterialPropertyValueD(propertyName)
            if valueD:
                shaderProperty.valueD = valueD

        texture_mapping_names = self.getMaterialTextureMappingNames()
        if texture_mapping_names:
            material.textureMapping.clear()
        for texture_mapping_name in texture_mapping_names:
            texture_name = self.getMaterialTextureMappingTextureName(texture_mapping_name)
            if not texture_name:
                self.warnings.append(f"Ignoring texture mapping '{texture_name}' for material '{material.name}' without texture name")
            else:
                material.textureMapping[texture_mapping_name] = texture_name

    def does_material_name_match(self, materialName):
        for regex in self.material_name_matches:
            if regex.match(materialName):
                return True
        return False

    def convert_to_matches_list(self, key):
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
        if "shaderName" in self.settings[MATERIALS][self.material_settings_key]:
            return self.settings[MATERIALS][self.material_settings_key]["shaderName"]
        return None

    def getMaterialBlendMode(self):
        if "alphaBlendMode" in self.settings[MATERIALS][self.material_settings_key]:
            return BlendMode[self.settings[MATERIALS][self.material_settings_key]["alphaBlendMode"]]
        return None

    def getMaterialDepthMode(self):
        if "depthMode" in self.settings[MATERIALS][self.material_settings_key]:
            return DepthMode[self.settings[MATERIALS][self.material_settings_key]["depthMode"]]
        return None

    def getMaterialAlphaTested(self):
        if "alphaTested" in self.settings[MATERIALS][self.material_settings_key]:
            return self.settings[MATERIALS][self.material_settings_key]["alphaTested"]
        return None

    def getMaterialPropertyNames(self):
        if "properties" in self.settings[MATERIALS][self.material_settings_key]:
            return self.settings[MATERIALS][self.material_settings_key]["properties"]
        return []

    def getMaterialPropertyValue(self, propertyName, valueName):
        if valueName in self.settings[MATERIALS][self.material_settings_key]["properties"][propertyName]:
            return self.settings[MATERIALS][self.material_settings_key]["properties"][propertyName][valueName]
        return None

    def getMaterialTextureMappingNames(self):
        if "textures" in self.settings[MATERIALS][self.material_settings_key]:
            return self.settings[MATERIALS][self.material_settings_key]["textures"]
        return []

    def getMaterialTextureMappingTextureName(self, mappingName):
        if "textures" in self.settings[MATERIALS][self.material_settings_key]:
            return self.settings[MATERIALS][self.material_settings_key]["textures"][mappingName]["texture_name"]
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
