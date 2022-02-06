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


ENCODING = 'utf-8'

KN5_HEADER_BYTES = b"sc6969"

ASSETTO_CORSA_OBJECTS = (
    r"AC_START_\d+",
    r"AC_PIT_\d+",
    r"AC_TIME_\d+_L",
    r"AC_TIME_\d+_R",
    r"AC_HOTLAP_START_\d+",
    r"AC_OPEN_FINISH_R",
    r"AC_OPEN_FINISH_L",
    r"AC_OPEN_START_L",
    r"AC_OPEN_START_R",
    r"AC_AUDIO_.+",
    r"AC_CREW_\d+",
    r"AC_PIT_\d+",
)
