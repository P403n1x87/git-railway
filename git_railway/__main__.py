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

from argparse import ArgumentParser
import os
import os.path

from git import InvalidGitRepositoryError, Repo
from git_railway.model import (
    arrange_commits,
    collect_commits,
    generate_commit_data,
    get_heads,
)
from git_railway.view.html import write_html
from git_railway.view.svg import SvgRailway


def parse_args():
    parser = ArgumentParser(prog="git-railway")

    parser.add_argument(
        "--gh",
        type=str,
        help="GitHub slug. If provided, issue references are replaced with links.",
    )

    parser.add_argument(
        "-o",
        "--output",
        type=str,
        help="Output file. If not provided, the default is railway.html in the current directory.",
        default="railway.html",
    )

    return parser.parse_args()


def main():
    try:
        repo = Repo(os.getcwd())
    except InvalidGitRepositoryError:
        print(
            "The current working directory doesn't seem to be tracked by a git repository."
        )
        exit(1)

    args = parse_args()

    commits, children = collect_commits(repo)
    heads = get_heads(repo)

    locations = arrange_commits(commits, heads, children)

    svg = SvgRailway()

    commit_data = generate_commit_data(commits, args.gh)

    output = os.path.abspath(os.path.expanduser(args.output)) or "railway.html"
    with open(output, "w") as fout:
        write_html(fout, svg.draw(commits, locations, heads, children), commit_data)

    print(f"🚂💨✨  Railway graph generated on file://{output}")


if __name__ == "__main__":
    main()
