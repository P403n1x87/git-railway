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

from functools import lru_cache
from hashlib import md5

from colour import Color
from git_railway.adt import IndexedList
from svgwrite import Drawing


@lru_cache(maxsize=32)
def ref_to_color(ref):
    color = Color(hex=f"#{md5(ref.name.encode()).hexdigest()[2:8]}")
    if color.saturation < 0.4:
        color.saturation = 0.4
    elif color.saturation > 0.5:
        color.saturation = 0.5

    if color.luminance < 0.6:
        color.luminance = 0.6
    elif color.luminance > 0.9:
        color.luminance = 0.9
    return color.get_hex()


class LayeredMixin:
    def __init__(self):
        self.layers = IndexedList()

    def add_layer(self, name):
        layer = []
        self.layers.append(name, layer)
        return layer

    def get_layer(self, name):
        return self.layers[self.layers.index(name)][1]


class SvgRailway(Drawing, LayeredMixin):
    STEP_X = 16
    STEP_Y = 28
    PADDING_X = 50
    PADDING_Y = 8
    STOP_R = 5
    RAIL_W = 6
    REF_A = 0

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        LayeredMixin.__init__(self)

        self.add_layer("rails")
        self.add_layer("stops")
        self.add_layer("labels")

    def rail(self, x, y, px, py, colors):
        # Move to the current commit
        layer = self.get_layer("rails")

        n = len(colors)
        w = self.RAIL_W / n
        dX = -(n - 1) / 2 * w
        for i, color in enumerate(colors):
            if x != px:
                # Parent commit is on a different level so we need to draw a
                # straight line up to the previous commit and then add a Bezier
                # curve to make a smooth connection
                v = x - px
                if v > 0:
                    path = self.path(
                        [
                            (
                                "M",
                                self.PADDING_X + x * self.STEP_X + dX + i * w,
                                self.PADDING_Y + self.STEP_Y * y,
                            )
                        ],
                        stroke=color,
                        stroke_width=w,
                        fill="none",
                    )
                    path.push("V", self.PADDING_Y + self.STEP_Y * (py - 1))
                    path.push(
                        "c",
                        0,
                        self.STEP_Y * (1 / 5),
                        -self.STEP_X * (1 / 4) * v,
                        self.STEP_Y * (2 / 5),
                        -self.STEP_X * (1 / 2) * v,
                        self.STEP_Y * (1 / 2),
                    )
                    path.push(
                        "c",
                        -self.STEP_X * (1 / 4) * v,
                        self.STEP_Y * (1 / 10),
                        -self.STEP_X * (1 / 2) * v,
                        self.STEP_Y * (3 / 10),
                        -self.STEP_X * (1 / 2) * v,
                        self.STEP_Y * (1 / 2),
                    )
                    layer.insert(0, path)
                else:
                    path = self.path(
                        [
                            (
                                "M",
                                self.PADDING_X + px * self.STEP_X + dX + i * w,
                                self.PADDING_Y + self.STEP_Y * py,
                            )
                        ],
                        stroke=color,
                        stroke_width=w,
                        fill="none",
                    )
                    path.push("V", self.PADDING_Y + self.STEP_Y * (y + 1))
                    path.push(
                        "c",
                        0,
                        -self.STEP_Y * (1 / 5),
                        self.STEP_X * (1 / 4) * v,
                        -self.STEP_Y * (2 / 5),
                        self.STEP_X * (1 / 2) * v,
                        -self.STEP_Y * (1 / 2),
                    )
                    path.push(
                        "c",
                        self.STEP_X * (1 / 4) * v,
                        -self.STEP_Y * (1 / 10),
                        self.STEP_X * (1 / 2) * v,
                        -self.STEP_Y * (3 / 10),
                        self.STEP_X * (1 / 2) * v,
                        -self.STEP_Y * (1 / 2),
                    )
                    layer.insert(0, path)

            else:
                path = self.path(
                    [
                        (
                            "M",
                            self.PADDING_X + x * self.STEP_X + dX + i * w,
                            self.PADDING_Y + self.STEP_Y * y,
                        )
                    ],
                    stroke=color,
                    stroke_width=w,
                    fill="none",
                )
                # Parent commit is at the same level so we just draw a straight.
                path.push("V", self.PADDING_Y + self.STEP_Y * py)
                layer.append(path)

    def stop(self, x, y, color, commit):
        self.get_layer("stops").append(
            self.circle(
                (self.PADDING_X + x * self.STEP_X, self.PADDING_Y + self.STEP_Y * y),
                self.STOP_R,
                fill=color,
                id=commit.hexsha,
                **{"class": "stop"},
            )
        )
        px, py = (self.PADDING_Y, self.PADDING_Y + y * self.STEP_Y + 2)
        self.get_layer("labels").append(
            self.text(
                commit.hexsha[:7],
                (px, py),
                fill="#c9bcbc",
                font_family="monospace",
                font_size="50%",
                # transform=f"rotate({self.REF_A}, {px}, {py})",
            )
        )

    def ref(self, ref, x, y, color, i=0):
        prefix = ""
        font_size = "65%"
        if hasattr(ref, "tag"):
            color = "#dad7bc"
            prefix = "🏷 "
            font_size = "55%"
        px, py = (
            self.PADDING_X + x * self.STEP_X + self.PADDING_Y,
            self.PADDING_Y + y * self.STEP_Y + 10 * i + 2,
        )
        self.get_layer("labels").append(
            self.text(
                prefix + ref.name,
                (px, py),
                fill=color,
                font_family="monospace",
                font_size=font_size,
                font_weight="bold",
                # transform=f"rotate({self.REF_A}, {px}, {py})",
            )
        )

    def draw(self, commits, locations, heads, children):
        max_y = max(y for _, (_, y) in locations.items())
        max_x = max(x for _, (x, _) in locations.items())

        height = max_y * self.STEP_Y + self.PADDING_Y * 2
        width = max_x * self.STEP_X + 2 * self.PADDING_X + 100
        self["viewBox"] = f"0 0 {width} {height}"
        self["height"] = height * 1.5
        self["width"] = width * 1.5

        # Add rails and stops
        for h, (commit, refs) in commits.items():
            x, y = locations[h]
            y = max_y - y
            for ph in [p.hexsha for p in commit.parents]:
                try:
                    px, py = locations[ph]
                    py = max_y - py
                except KeyError:
                    # If some branches are deleted (or we ignore remotes) then
                    # some parent commits will be missing
                    continue
                _, prefs = commits[ph]

                try:
                    common = set(prefs) & set(refs)
                    if len(refs) > 1 and common:
                        colors = [ref_to_color(ref) for ref in common]

                    else:
                        used_refs = {
                            ref for child in children[ph] for ref in commits[child][1]
                        }
                        colors = [
                            ref_to_color(ref)
                            for ref in (
                                refs
                                if common or len(commit.parents) <= 1
                                else prefs - used_refs
                            )
                        ]
                except IndexError:
                    colors = ["gray"]
                if not colors:
                    colors = ["gray"]
                self.rail(x, y, px, py, colors)

            # try:
            #     if len(refs) > 1 and common:
            #         color = ref_to_color(sorted(list(common), key=lambda x: x.name)[0])
            #     else:
            #         color = ref_to_color(sorted(list(refs), key=lambda x: x.name)[0])
            # except IndexError:
            #     color = "gray"
            self.stop(x, y, "#dbdbdb", commit)

        for h, refs in heads.items():
            x, y = locations[h]
            y = max_y - y
            for i, ref in enumerate(refs):
                self.ref(ref, max_x, y, ref_to_color(ref), i)

        for _, layer in self.layers:
            for e in layer:
                self.add(e)

        return self.tostring()
