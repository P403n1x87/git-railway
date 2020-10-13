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

from collections import defaultdict
from functools import lru_cache
from hashlib import md5

from colour import Color
from git import TagReference
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
    STEP_X = 24
    STEP_Y = 30
    PADDING_X = 50
    PADDING_Y = 8
    STOP_R = 5
    RAIL_W = 6
    REF_A = 0

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs, id="railway_svg")
        LayeredMixin.__init__(self)

        self.add_layer("rails")
        self.add_layer("stops")
        self.add_layer("labels")

    @staticmethod
    def _add_s(path, dx=1, dy=1):
        # TODO: Use vectors
        path.push(
            "c",
            0,
            SvgRailway.STEP_Y * (1 / 5) * dy,
            -SvgRailway.STEP_X * (1 / 4) * dx,
            SvgRailway.STEP_Y * (2 / 5) * dy,
            -SvgRailway.STEP_X * (1 / 2) * dx,
            SvgRailway.STEP_Y * (1 / 2) * dy,
        )
        path.push(
            "c",
            -SvgRailway.STEP_X * (1 / 4) * dx,
            SvgRailway.STEP_Y * (1 / 10) * dy,
            -SvgRailway.STEP_X * (1 / 2) * dx,
            SvgRailway.STEP_Y * (3 / 10) * dy,
            -SvgRailway.STEP_X * (1 / 2) * dx,
            SvgRailway.STEP_Y * (1 / 2) * dy,
        )

    def rail(self, x, y, px, py, colors, middle):
        # Move to the current commit
        layer = self.get_layer("rails")

        n = len(colors)
        w = self.RAIL_W / n
        dX = -(n - 1) / 2 * w
        dx = x - px
        for i, color in enumerate(colors):
            if middle:
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
                if dx:
                    dl = dr = dx
                    if dl & 1 == 0:
                        dl -= 1
                        dr += 1
                    SvgRailway._add_s(path, dl / 2)
                    path.push("V", self.PADDING_Y + self.STEP_Y * (py - 1))
                    SvgRailway._add_s(path, dr / 2)
                else:
                    SvgRailway._add_s(path, -0.5)
                    path.push("V", self.PADDING_Y + self.STEP_Y * (py - 1))
                    SvgRailway._add_s(path, 0.5)

                layer.insert(0, path)

            elif dx:
                # Parent commit is on a different level so we need to draw a
                # straight line up to the previous commit and then add a Bezier
                # curve to make a smooth connection
                if dx > 0:
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
                    SvgRailway._add_s(path, dx)
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
                    SvgRailway._add_s(path, -dx, -1)
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
                font_family="Ubuntu Mono",
                font_size="50%",
                # transform=f"rotate({self.REF_A}, {px}, {py})",
            )
        )

    def refs(self, refs, x, y):
        px, py = (
            self.PADDING_X + x * self.STEP_X + self.PADDING_Y,
            self.PADDING_Y + y * self.STEP_Y + 2,
        )
        text = self.text("", (px, py))
        for ref in refs:
            if isinstance(ref, TagReference):
                color = "#dad7bc"
                prefix = "🏷 "
            else:
                color = ref_to_color(ref)
                prefix = ""
            text.add(
                self.tspan(
                    prefix + ref.name + " ",
                    fill=color,
                    font_family="Ubuntu Mono",
                    font_size="60%",
                    font_weight="bold",
                )
            )
        self.get_layer("labels").append(text)

    def draw(self, commits, locations, heads, tags, children):
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
            singletons = {
                ref
                for p in commit.parents
                for ref in commits[p.hexsha][1]
                if len(commits[p.hexsha][1]) == 1
            }
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
                        colors = [
                            ref_to_color(ref)
                            for ref in common
                            if len(prefs) == 1 or ref not in singletons
                        ]

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

                colors = colors or (
                    [ref_to_color(ref) for ref in refs] if refs and prefs else ["gray"]
                )

                self.rail(
                    x,
                    y,
                    px,
                    py,
                    colors,
                    any(
                        True
                        for _, (rx, ry) in locations.items()
                        if rx == (px if px > x else x) and py > max_y - ry > y
                    ),
                )

            # try:
            #     if len(refs) > 1 and common:
            #         color = ref_to_color(sorted(list(common), key=lambda x: x.name)[0])
            #     else:
            #         color = ref_to_color(sorted(list(refs), key=lambda x: x.name)[0])
            # except IndexError:
            #     color = "gray"
            color = "#ff4545" if "BREAKING CHANGE: " in commit.message else "#dbdbdb"
            self.stop(x, y, color, commit)

        refs = defaultdict(list)

        for h, r in tags.items():
            refs[h] += r
        for h, r in heads.items():
            refs[h] += r

        for h, r in refs.items():
            x, y = locations[h]
            y = max_y - y
            self.refs(r, x, y)

        for _, layer in self.layers:
            for e in layer:
                self.add(e)

        return self.tostring()
