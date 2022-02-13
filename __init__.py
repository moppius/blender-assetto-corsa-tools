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


from . import exporter, importer, ui
from .utils import register_recursive, unregister_recursive


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


REGISTER_CLASSES = (
    exporter,
    importer,
    ui,
)


def register():
    """Register all of the addon's classes."""
    register_recursive(REGISTER_CLASSES)


def unregister():
    """Unregister all of the addon's classes."""
    unregister_recursive(REGISTER_CLASSES)


if __name__ == "__main__":
    register()
