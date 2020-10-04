# This file is part of "git-railway" which is released under GPL.
#
# See file LICENCE or go to http://www.gnu.org/licenses/ for full license
# details.
#
# git-railway is top-like TUI for Austin.
#
# Copyright (c) 2018-2020 Gabriele N. Tornetta <phoenix1987@gmail.com>.
# All rights reserved.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


class IndexedList(list):
    """List with an underlying index for fast lookups."""

    def __init__(self):
        super().__init__()

        self._index = {}

    def append(self, k, v):
        self._index[k] = len(self)
        super().append((k, v))

    def index(self, k):
        return self._index[k]

    def __contains__(self, k):
        return k in self._index

    def truncate(self, i):
        for k, _ in self[i:]:
            del self._index[k]
        del self[i:]

    def pop(self):
        del self._index[super().pop()[0]]
