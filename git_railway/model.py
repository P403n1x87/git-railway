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
import re
from typing import Dict, List, Set, Tuple

from git_railway.adt import Map
from git import Head, Repo, Commit, Reference, TagReference


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

    if day_diff == 0:
        return "Today"
    if day_diff == 1:
        return "Yesterday"
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
    repo: Repo
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

    # Collect all the commits that are reachable from the current heads
    for head in repo.heads:
        add_commits(head.commit)

    # Look at the reflog to infer what ref was on which commit.
    labelled_commits = {h: (c, set()) for h, c in commits.items()}
    for head in repo.heads:
        for h in [e.newhexsha for e in head.log()]:
            try:
                labelled_commits[h][1].add(head)
            except KeyError:
                pass

    return labelled_commits, children


def get_heads(repo: Repo) -> Dict[Hash, List[Reference]]:
    """Get all the current heads, indexed by commit hash.

    Used to easily determine which commits are heads and what refs are on them.
    """
    heads = defaultdict(list)
    for head in repo.heads:
        heads[head.commit.hexsha].append(head)
    for tag in repo.tags:
        heads[tag.commit.hexsha].append(tag)

    return heads


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
    sorted_commits = sorted(commits.items(), key=lambda x: x[1][0].committed_date)
    h, (initial, refs) = sorted_commits[0]  # Initial commit

    # Filter out tags.
    heads = {
        head: [r for r in heads[head] if isinstance(r, Head)]
        for head, refs in heads.items()
        if [r for r in heads[head] if isinstance(r, Head)]
    }  # TODO: Suboptimal!

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

    # head_children = {h: head_children.preimage(h) for h in heads}
    locations = {h: (0, 0)}

    for h, (c, refs) in sorted_commits[1:]:
        try:
            m = max(l for _, l in refs_levels.items())  # Max height
        except ValueError:
            m = -1

        if not refs:
            # The commit has no ref history so we don't know which branches it
            # belonged to.
            # if len(c.parents) == 1 and len(allchildren[c.parents[0].hexsha]) > 1:
            if len(c.parents) == 1 and len(children[c.parents[0].hexsha]) > 1:
                # The commit has exactly one parent. The parent has more than 1
                # child. Therefore we should try to move this up to allow
                # rails to move to the other children.
                x = m + 1 if m >= 0 else 1
            else:
                # All the parents of this commit have only one child. Therefore
                # we pick the parent with the lowest height.
                x = min(
                    w for w, _ in [locations[k] for k in [p.hexsha for p in c.parents]]
                )
        else:
            # Pick the common parent ref with the lowest height, if any;
            # otherwise go up by 1 from the current maximum height.
            x = min(
                [m + 1]
                + [l for r, l in refs_levels.items() if r in (set(refs_levels) & refs)]
            )

        # If refs is a proper subset of the tracked refs at the level y then
        # we need a new level as we have diverged.
        if refs and {ref for ref, level in refs_levels.items() if level == x} > refs:
            x = m + 1

        locations[h] = (x, len(locations))

        # Update the levels of the tracked refs
        for ref in refs:
            refs_levels[ref] = x

        if h in heads:
            # Mark the head for untracking
            seen_heads.add(h)
        elif h in children_head:
            # Remove the child from the set of children of all its parent heads
            for head in children_head[h]:
                head_children[head].remove(h)

        # Check if we can untrack any marked heads (i.e. we have already seen
        # all its child commits).
        for head in set(seen_heads):
            if not head_children[head]:
                seen_heads.remove(head)
                try:
                    for ref in heads[head]:
                        del refs_levels[ref]
                except KeyError:
                    pass

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

    return {
        h: {
            "hash": h[:7],
            "author": f'<a href="mailto:{c.author.email}">{c.author.name}</a>',
            "committer": f'<a href="mailto:{c.committer.email}">{c.committer.name}</a>',
            "title": issue_link(c.summary),
            "message": issue_link(c.message.replace(c.summary, "", 1))
            .strip()
            .replace(" \n", " ")
            .replace(" \r\n", " "),
            "authored_date": str(c.authored_datetime),
            "committed_date": str(c.committed_datetime),
            "authored_date_delta": pretty_date(c.authored_date),
            "committed_date_delta": pretty_date(c.committed_date),
        }
        for h, (c, _) in commits.items()
    }
