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
    get_refs,
)
from git_railway.view.html import write_html
from git_railway.view.svg import SvgRailway


def parse_args():
    parser = ArgumentParser(prog="git-railway")

    parser.add_argument(
        "-a",
        "--all",
        action="store_true",
        help="Show all branches, including remote ones.",
        default=False,
    )

    parser.add_argument(
        "--gh",
        type=str,
        help="GitHub slug override. If not provided, there will be an attempt to "
        "derive it from the repository remotes.",
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
    cwd = os.getcwd()
    path = cwd
    while True:
        try:
            repo = Repo(path)
            break
        except InvalidGitRepositoryError:
            newpath = os.path.dirname(path)
            if newpath == path:
                print("👮‍♀️🛑  Not in a git repository")
                exit(1)
            path = newpath

    args = parse_args()

    commits, children = collect_commits(repo, args.all)
    heads, tags = get_refs(repo, args.all)

    locations = arrange_commits(commits, heads, children)

    svg = SvgRailway()

    try:
        gh_url, *_ = [
            url for remote in repo.remotes for url in remote.urls if "github.com" in url
        ]
        _, _, gh_slug = gh_url.replace(".git", "").partition("github.com/")
    except Exception:
        gh_slug = None

    commit_data = generate_commit_data(commits, args.gh or gh_slug)

    output = os.path.abspath(os.path.expanduser(args.output)) or "railway.html"
    with open(output, "wb") as fout:
        write_html(
            fout,
            svg.draw(commits, locations, heads, tags, children),
            commit_data,
            title=os.path.basename(path),
        )

    print(f"🚂💨  Railway graph generated on ✨ file://{output} ✨")


if __name__ == "__main__":
    main()
