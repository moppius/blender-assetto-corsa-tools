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


import json
import os
from inspect import isclass
import bpy
from mathutils import Matrix, Vector, Quaternion


def register_recursive(objects):
    """Registers classes with Blender recursively from modules."""
    for obj in objects:
        if isclass(obj):
            bpy.utils.register_class(obj)
        elif hasattr(obj, "register"):
            obj.register()
        elif hasattr(obj, "REGISTER_CLASSES"):
            register_recursive(obj.REGISTER_CLASSES)
        else:
            print(f"Warning: Failed to find anything to register for '{obj}'")


def unregister_recursive(objects):
    """Unregisters classes from Blender recursively from modules."""
    for obj in reversed(objects):
        if isclass(obj):
            bpy.utils.unregister_class(obj)
        elif hasattr(obj, "unregister"):
            obj.unregister()
        elif hasattr(obj, "REGISTER_CLASSES"):
            unregister_recursive(obj.REGISTER_CLASSES)
        else:
            print(f"Warning: Failed to find anything to unregister for '{obj}'")
