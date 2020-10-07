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
git checkout -b devel

# * <- main, devel

sleep 2
git checkout -b "feature"
echo "feature" > feature
git add .
git commit -m "feature"

# * <- feature
# |
# * <- main, devel

sleep 2
git checkout devel
git merge --no-ff feature

#   * <- devel
#  /|
# | * <-feature
# |/
# * <- main

sleep 2
git checkout main
git merge --no-ff devel
git checkout devel
git merge main

# *
# |\
# | * <- devel
# |/|
# | * <-feature
# |/
# * <- main
