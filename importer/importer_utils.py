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


import struct
from mathutils import Matrix


ENCODING = 'utf-8'


def read_string(file):
    str_len = read_int(file)
    binary_string = struct.unpack(f"{str_len}s", file.read(str_len))[0]
    return binary_string.decode(ENCODING)


def read_uint(file):
    return struct.unpack("I", file.read(struct.calcsize("I")))[0]


def read_int(file):
    return struct.unpack("i", file.read(struct.calcsize("i")))[0]


def read_ushort(file):
    return struct.unpack("H", file.read(struct.calcsize("H")))[0]


def read_byte(file):
    return struct.unpack("B", file.read(struct.calcsize("B")))[0]


def read_bool(file):
    return struct.unpack("?", file.read(struct.calcsize("?")))[0]


def read_float(file):
    return struct.unpack("f", file.read(struct.calcsize("f")))[0]


def read_vector2(file):
    return struct.unpack("2f", file.read(struct.calcsize("2f")))[0]


def read_vector3(file):
    return struct.unpack("3f", file.read(struct.calcsize("3f")))[0]


def read_vector4(file):
    return struct.unpack("4f", file.read(struct.calcsize("4f")))[0]


def read_matrix(file):
    matrix = Matrix()
    for r in range(4):
        for c in range(4):
            matrix[c][r] = read_float(file)
    return matrix
