# aprslib - Python library for working with APRS
# Copyright (C) 2013-2014 Rossen Georgiev
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

"""
APRS library in Python

Currently the library provides facilities to:
    - parse APRS packets
    - Connect and listen to an aprs-is packet feed
"""

# Py2 & Py3 compability
import sys
if sys.version_info[0] >= 3:
    is_py3 = True
    string_type = (str, )
    string_type_parse = string_type + (bytes, )
    int_type = int
else:
    is_py3 = False
    string_type = (str, unicode)
    string_type_parse = string_type
    int_type = (int, long)

# handles reloading
if 'IS' in globals():
    MODULES = __import__('sys').modules
    for M in MODULES.keys():
        if M[:len(__name__)+1] == "%s." % __name__:
            del MODULES[M]

    del MODULES
    del M

from datetime import date as _date
__date__ = str(_date.today())
del _date

__version__ = "0.6.40"
__author__ = "Rossen Georgiev"
__all__ = ['IS', 'parse', 'passcode']

from .exceptions import *
from .parsing import parse
from .passcode import passcode

from .IS import IS


class IS(IS):
    pass
