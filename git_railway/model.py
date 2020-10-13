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
from datetime import datetime
import logging
import os
import re
from typing import Dict, List, Set, Tuple

from git_railway.adt import Map
from git import Head, Repo, Commit, Reference, TagReference


LOGGER = logging.getLogger()
handler = logging.StreamHandler()
handler.setFormatter(
    logging.Formatter("%(asctime)s %(name)-12s %(levelname)-8s %(message)s")
)
LOGGER.addHandler(handler)
LOGGER.setLevel(
    getattr(logging, os.environ.get("GIT_RAILWAY_DEBUG_LEVEL", "INFO").upper())
)


ISSUE_RE = re.compile("#([0-9]+)")

Hash = str


def pretty_date(time: int) -> str:
    """Format a time delta in pretty, human-readable format.

    E.g. '3 months ago'.
    """
    now = datetime.now()
    diff = now - datetime.fromtimestamp(time)
    day_diff = diff.days

    def ago(n, what, suffix=True):
        return f"{n} {what}{'s' if n > 1 else ''}" + (" ago" if suffix else "")

    if day_diff < 0:
        return ""

    if day_diff <= 1:
        return "a day ago"
    if day_diff < 7:
        return f"{day_diff} days ago"
    if day_diff < 31:
        weeks = int(day_diff / 7)
        return ago(weeks, "week")
    months = int(day_diff / (365 / 12))
    if day_diff < 365:
        return ago(months, "month")

    years = int(day_diff / 365)
    months %= 12
    if months < 1:
        return ago(years, "year")

    return ago(years, "year", suffix=False) + ", " + ago(months, "month")


def collect_commits(
    repo: Repo, all: bool = False
) -> Tuple[Dict[Hash, Tuple[Commit, Set[Reference]]], Dict[Hash, Set[Hash]]]:
    """Collect commit information from a repository.

    The return value is a tuple consisting of a dictionary of all the commits
    that are reachable from the current heads and a dictionary of commit hashes
    mapping to all their children. Both dictionary are indexed by commit
    hashes. The values of the first one are pairs consisting of the actual
    commit object together with all the references that have been attached to
    it over time; this information is reconstructed from the reflogs. The
    second dictionary has set of commit hashes of child commits as values.
    """
    commits: Dict[Hash, Tuple[Commit, Set[Reference]]] = {}
    children: Dict[Hash, Set[Hash]] = defaultdict(set)

    def add_commits(commit: Commit) -> None:
        """Add commits recursively"""
        if commit.hexsha in commits:
            return

        commits[commit.hexsha] = commit
        for p in commit.parents:
            children[p.hexsha].add(commit.hexsha)
            add_commits(p)

    tracking = Map()

    # Collect all the commits that are reachable from the current heads
    for head in repo.heads:
        remote_ref = head.tracking_branch()
        if remote_ref:
            tracking[remote_ref] = head
        add_commits(head.commit)

    for tag in repo.tags:
        if tag.commit.hexsha not in commits:
            add_commits(tag.commit)

    if all:
        remote_refs = [ref for remote in repo.remotes for ref in remote.refs]
        for ref in remote_refs:
            add_commits(ref.commit)

    # Look at the reflog to infer what ref was on which commit.
    labelled_commits = {h: (c, set()) for h, c in commits.items()}
    for head in repo.heads:
        for h in [e.newhexsha for e in head.log()]:
            try:
                labelled_commits[h][1].add(head)
                # if head in tracking.image:
                #     labelled_commits[h][1].add(tracking.inv(head))
            except KeyError:
                pass

    if all:
        for ref in [
            ref for remote in repo.remotes for ref in remote.refs if ref not in tracking
        ]:
            for h in [e.newhexsha for e in ref.log()]:
                try:
                    labelled_commits[h][1].add(ref)
                except KeyError:
                    pass

    return labelled_commits, children


def get_refs(
    repo: Repo, all: bool = False
) -> Tuple[Dict[Hash, List[Head]], Dict[Hash, List[TagReference]]]:
    """Get all the current heads and tags, indexed by commit hash.

    Used to easily determine which commits are heads and what refs are on them.
    """
    heads = defaultdict(list)
    for head in repo.heads:
        heads[head.commit.hexsha].append(head)

    if all:
        for ref in [ref for remote in repo.remotes for ref in remote.refs]:
            heads[ref.commit.hexsha].append(ref)

    tags = defaultdict(list)
    for tag in repo.tags:
        tags[tag.commit.hexsha].append(tag)

    return heads, tags


def arrange_commits(
    commits: Dict[Hash, Tuple[Commit, Set[Reference]]],
    heads: Dict[Hash, List[Reference]],
    children: Dict[Hash, Set[Hash]],
) -> Dict[Hash, Tuple[int, int]]:
    """Arrange commits over a lattice.

    Use the head and children information of all the collected commits to
    determine the best spatial position for each commit. From one hand we want
    to avoid crossing rails, from the other we do not want the width of the
    lattice to grow without control.
    """

    def ctsort():
        """Chrono-topological sort.

        Implement a variant of Kahn's algorithm for topological sorting where
        time ordering is also taken into account.
        """
        sorted_commits = sorted(commits.items(), key=lambda x: x[1][0].committed_date)
        parents = {h: {p.hexsha for p in commits[h][0].parents} for h in commits}
        result = []
        while sorted_commits:
            i = 0
            while True:
                if not parents[sorted_commits[i][0]]:
                    c = sorted_commits.pop(i)
                    result.append(c)
                    h = c[0]
                    for child in children[h]:
                        parents[child].remove(h)
                    break
                i += 1

        return result

    def gap(refs=True) -> int:
        """Get the first gap in the tracked levels."""
        if not refs_levels:
            return 0 if refs else 1

        levels = sorted({l for _, l in refs_levels.items()})
        for n, m in zip(levels, levels[1:]):
            if m - n > 1:
                return n + 1

        return levels[-1] + 1

    sorted_commits = ctsort()
    h, (initial, refs) = sorted_commits[0]  # Initial commit

    # Map the head commits with their children.
    head_children = {
        h: set(children[h])
        for h in heads
        if [r for r in heads[h] if isinstance(r, Head)]
    }
    children_head = defaultdict(set)
    for head, cs in head_children.items():
        for c in cs:
            children_head[c].add(head)

    # Keep track of branch heights. If we find the head of a branch we can stop
    # tracking it thus allowing another branch to be placed on the same level,
    # avoiding an ever growing railway graph.
    refs_levels = {ref: 0 for ref in refs}
    seen_heads = set()

    locations = {h: (0, 0)}
    for i, (h, (c, refs)) in enumerate(sorted_commits[1:]):
        x = None
        active_refs = set(refs_levels)
        LOGGER.debug(f"{h[:7]} :: refs: {str([r.name for r in refs])}")
        if not refs:  # Commit has no refs
            # Take the position of the lowest parent
            p, x = sorted(
                [(p.hexsha, locations[p.hexsha][0]) for p in c.parents],
                key=lambda x: x[1],
            )[0]
            future_children = {
                child
                for child in children[p]
                if child in {h for h, _ in sorted_commits[i + 2 :]}
            }
            if future_children:
                x = gap(refs=False)

            LOGGER.debug(f"  no refs, x = {x}, future_children = {future_children}")

        elif not refs & set(refs_levels):  # Commit has new refs only
            LOGGER.debug("  new refs only")
            # For each parent, look at the future children wrt to the current
            # commit and count those with only new refs or those whose refs
            # are a superset of the parent's refs. Then take the minimum.
            x = gap()
        else:  # Commit has tracked refs
            LOGGER.debug("  commit has tracked refs")
            px = {}
            m = max(l for _, l in refs_levels.items())
            for p in c.parents:
                # If the commit has the same tracked refs as the parent then
                # put on the same level as parent. Else put on one of the
                # lowest refs if they are on a different level than the parent
                current_refs = refs & active_refs
                LOGGER.debug(
                    f"    {str([r.name for r in current_refs])}"
                    " =?= "
                    f"{str([r.name for r in commits[p.hexsha][1] & active_refs])}"
                )
                if current_refs == commits[p.hexsha][1] & active_refs:
                    x = locations[p.hexsha][0]
                    LOGGER.debug(
                        f"  same as parent {p.hexsha[:7]} :: x = {x}, px = {locations[p.hexsha][0]}"
                    )

                elif any(
                    {r for r, j in refs_levels.items() if j == i and r in current_refs}
                    < commits[p.hexsha][1] & active_refs
                    for i in {l for _, l in refs_levels.items()}
                ):
                    # currently active refs on commit are a proper subset of
                    # currently active parent refs at each tracked level.
                    LOGGER.debug(
                        f"    {h[:7]} diverged from parent: {current_refs} < {commits[p.hexsha][1]}"
                    )
                    # try lowest ref
                    x = min(refs_levels[ref] for ref in current_refs)
                    LOGGER.debug(
                        f"    {x} =?= {locations[p.hexsha][0]} :: {[r.name for r in commits[p.hexsha][1]]} <?= {[r.name for r in active_refs]}"
                    )
                    if x == locations[p.hexsha][0]:
                        # lowest ref is same level as parent but we have
                        # diverged from this parent so we must go on a
                        # different level.
                        x = gap()
                        LOGGER.debug(f"      need a new level: m = {m}, x = {x}")
                elif not commits[p.hexsha][1]:  # parent has no refs
                    x = locations[p.hexsha][0]  # use parent level
                else:
                    x = gap()
                    LOGGER.debug(f"    new level: {x}")

                px[p.hexsha] = x
            x = min(l for _, l in px.items())

        locations[h] = (x, len(locations))

        # Update the levels of the tracked refs
        for ref in refs:
            refs_levels[ref] = x

        if h in heads:
            # Mark the head for untracking
            seen_heads.add(h)
            LOGGER.debug(f"  seen head at {h}")
        elif h in children_head:
            # Remove the child from the set of children of all its parent heads
            for head in children_head[h]:
                head_children[head].remove(h)

        for head in set(seen_heads):
            seen_heads.remove(head)
            try:
                for ref in heads[head]:
                    del refs_levels[ref]
                    LOGGER.debug(f"  removed {ref.name}")
            except KeyError:
                pass

        LOGGER.debug(f"  new levels:{[(r.name, l) for r, l in refs_levels.items()]}")
    return locations


def generate_commit_data(
    commits: Dict[Hash, Tuple[Commit, Set[Reference]]], gh: str = None
) -> Dict[Hash, dict]:
    """Generate the commit data to be displayed."""

    def issue_link(text):
        return (
            ISSUE_RE.sub(
                f'<a target="_blank" href="https://github.com/{gh}/issues/\g<1>">#\g<1></a>',
                text,
            )
            if gh
            else text
        )

    def conv_commit(text):
        text = issue_link(text)
        if ": " not in text:
            return {"type": None, "scope": None, "title": text}

        cc, _, title = text.partition(": ")
        type, _, scope = cc.strip(")").partition("(")
        if " " in type:
            return {"type": None, "scope": None, "title": text}

        return {"type": type, "scope": scope, "title": title}

    def message(commit):
        result = conv_commit(issue_link(commit.summary))
        result["body"] = (
            issue_link(commit.message.replace(commit.summary, "", 1))
            .strip()
            .replace(" \n", " ")
            .replace(" \r\n", " ")
        )
        result["is_breaking"] = "BREAKING CHANGE: " in commit.message

        return result

    return {
        h: {
            "hash": h[:7],
            "author": f'<a href="mailto:{c.author.email}">{c.author.name}</a>',
            "committer": f'<a href="mailto:{c.committer.email}">{c.committer.name}</a>',
            "message": message(c),
            "authored_date": str(c.authored_datetime),
            "committed_date": str(c.committed_datetime),
            "authored_date_delta": pretty_date(c.authored_date),
            "committed_date_delta": pretty_date(c.committed_date),
        }
        for h, (c, _) in commits.items()
    }
