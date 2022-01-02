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


ENCODING = 'utf-8'


class KN5Writer():
    def __init__(self, file):
        self.file = file

    def write_string(self, string):
        string_bytes = string.encode(ENCODING)
        self.write_uint(len(string_bytes))
        self.file.write(string_bytes)

    def write_blob(self, blob):
        self.write_uint(len(blob))
        self.file.write(blob)

    def write_uint(self, int_val):
        self.file.write(struct.pack("I", int_val))

    def write_int(self, int_val):
        self.file.write(struct.pack("i", int_val))

    def write_ushort(self, short):
        self.file.write(struct.pack("H", short))

    def write_byte(self, byte):
        self.file.write(struct.pack("B", byte))

    def write_bool(self, bool_val):
        self.file.write(struct.pack("?", bool_val))

    def write_float(self, f):
        self.file.write(struct.pack("f", f))

    def write_vector2(self, vector2):
        self.file.write(struct.pack("2f", *vector2))

    def write_vector3(self, vector3):
        self.file.write(struct.pack("3f", *vector3))

    def write_vector4(self, vector4):
        self.file.write(struct.pack("4f", *vector4))

    def write_matrix(self, matrix):
        for row in range(4):
            for col in range(4):
                self.write_float(matrix[col][row])
