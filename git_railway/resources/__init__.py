# This file is part of "git-railway" which is released under GPL.
#
# See file LICENCE or go to http://www.gnu.org/licenses/ for full license
# details.
#
# git-railway is a visualisation tool for git branches.
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

from typing import Optional, Tuple

from importlib_resources import files


def _find_marker(
    text: str, ldel: str, rdel: str, begin: int
) -> Optional[Tuple[int, int, str]]:
    begin = text.find(ldel, begin)
    if begin < 0:
        return None
    end = text.find(rdel, begin) + len(rdel)

    return begin, end, text[begin:end]


def get_resource(name: str, **kwargs: dict) -> str:
    """Load a resource file."""
    return replace_placeholders(
        replace_references(files(__name__).joinpath(name).read_text(encoding="utf-8")),
        **kwargs
    )


def replace_placeholders(text: str, **kwargs: str) -> str:
    """Replace occurrences of ((% placeholder %)) with the given keyword arguments."""
    if not kwargs:
        return text

    begin = 0
    while True:
        marker = _find_marker(text, r"((%", r"%))", begin)
        if not marker:
            break

        begin, end, placeholder = marker

        key = placeholder[3:-3].strip()
        value = kwargs.get(key)

        if not value:
            begin += 3
            continue

        text = text.replace(placeholder, value)

        begin += len(value)

    return text


def replace_references(text: str) -> str:
    """Replace {{ reference }} with the content of the referenced resource."""
    begin = 0
    while True:
        marker = _find_marker(text, "{{", "}}", begin)
        if not marker:
            break

        begin, end, placeholder = marker

        reference = placeholder[2:-2].strip()
        resource = get_resource(reference)

        text = text.replace(placeholder, replace_references(resource))

        begin += len(resource)

    return text
