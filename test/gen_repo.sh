#!/bin/bash

set -e

cd /tmp
test -d testrepo && rm -rf testrepo
mkdir testrepo
cd testrepo

git init

echo "A" > README
git add .
git commit -m "Initial commit"
git branch -M main

# * <- main

git checkout -b devel
echo "dev" > dev
git add .
git commit -m "dev"

#   * <- devel
#  /
# * <- main

git checkout main
git checkout -b "feature"
echo "feature" > feature
git add .
git commit -m "feature"

#   * <- feature
#  /
# | * <- devel
# |/
# * <- main

git checkout main
echo "release" > release
git add .
git commit -m "release"

# * <- main
# | * <- feature
# |/
# | * <- devel
# |/
# *
