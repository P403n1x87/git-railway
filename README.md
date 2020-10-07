<h1 align="center">Git Railway</h1>

<h3 align="center">Visualise local git branches as neat interactive HTML pages</h3>

<p align="center">
  <img src="https://upload.wikimedia.org/wikipedia/commons/3/3a/Tux_Mono.svg"
       height="24px" />
  &nbsp;&nbsp;&nbsp;&nbsp;
  <img src="https://upload.wikimedia.org/wikipedia/commons/f/fa/Apple_logo_black.svg"
       height="24px" />
  &nbsp;&nbsp;&nbsp;&nbsp;
  <img src="https://upload.wikimedia.org/wikipedia/commons/2/2b/Windows_logo_2012-Black.svg"
       height="24px" />
</p>

<p align="center">
  <!-- <a href="https://github.com/P403n1x87/git-railway/actions?workflow=Tests">
    <img src="https://github.com/P403n1x87/git-railway/workflows/Tests/badge.svg"
         alt="GitHub Actions: Tests">
  </a> -->
  <a href="https://travis-ci.com/P403n1x87/git-railway">
    <img src="https://travis-ci.com/P403n1x87/git-railway.svg?token=fzW2yzQyjwys4tWf9anS"
         alt="Travis CI">
  </a>
  <!-- <a href="https://codecov.io/gh/P403n1x87/git-railway">
    <img src="https://codecov.io/gh/P403n1x87/git-railway/branch/master/graph/badge.svg"
         alt="Codecov">
  </a> -->
  <a href="https://pypi.org/project/git-railway/">
    <img src="https://img.shields.io/pypi/v/git-railway.svg"
         alt="PyPI">
  </a>
  <a href="https://github.com/P403n1x87/git-railway/blob/master/LICENSE.md">
    <img src="https://img.shields.io/badge/license-GPLv3-ff69b4.svg"
         alt="LICENSE">
  </a>
</p>

<p align="center">
  <!-- <a href="#synopsis"><b>Synopsis</b></a>&nbsp;&bull; -->
  <a href="#installation"><b>Installation</b></a>&nbsp;&bull;
  <a href="#usage"><b>Usage</b></a>
	<!-- &nbsp;&bull; -->
  <!-- <a href="#compatibility"><b>Compatibility</b></a>&nbsp;&bull;
  <a href="#contribute"><b>Contribute</b></a> -->
</p>

<p align="center">
	<img alt="Git Railway Example"
	     src="art/sample.png" />
</p>

# Installation

Installation from the repository requires Poetry

~~~
pip install poetry git+https://github.com/p403n1x87/git-railway
~~~

Soon available from PyPI!


# Usage

Navigate to a git repository and run

~~~ shell
git-railway
~~~

Your railway graph will be generated in `railway.html`. Use the `-o` or
`--output` option to override the default location, e.g.

~~~ shell
git-railway --output /tmp/mytemprailwaygraph.html
~~~

If the remote repository is hosted on GitHub, you can have issue and PR
references replaced with actual links if you pass the GitHub slug using the
`--gh` option, e.g.

~~~ shell
git-railway --gh p403n1x87/git-railway
~~~


# A word on branches

As you probably know already, a branch in git is a mere reference (or label)
that moves with every new commit. As such, it's hard if not impossible to
reconstruct the *actual* branch from the information available from within a git
repository. This tools works by looking at the current local refs and collecting
all the commits that can be reached from them. The "branches" are the
reconstructed "best effort" by looking at the reflog to determine on which
commit a certain ref has been on. Sometimes this information is missing. For
example, when one does a merge by fast-forwarding, all the intermediate commits
are not marked with the ref of the target branch. Should they be part of the
branch or not? Whenever you see a piece of gray rail in the graph, that's where
the ref information is missing.
