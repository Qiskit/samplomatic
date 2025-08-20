#!/usr/bin/env sh
set -euo pipefail

# Grab the version argument
if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <version>"
    exit 1
fi
VERSION="$1"

# Have to be on the main branch
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
if [ "$CURRENT_BRANCH" != "main" ]; then
    echo "Error: you must be on the 'main' branch (currently on '$CURRENT_BRANCH')."
    exit 1
fi

echo "=================================================================="
echo "Checking out a new branch ..."
echo "=================================================================="
BRANCH_NAME="release-$VERSION"
if git show-ref --verify --quiet "refs/heads/$BRANCH_NAME"; then
    echo "Error: branch '$BRANCH_NAME' already exists."
    exit 1
fi
git checkout -b "$BRANCH_NAME"

echo "=================================================================="
echo "Building the changelog ..."
echo "=================================================================="
towncrier build --yes --version "$VERSION"

echo ""
echo "=================================================================="
echo "Committing the changelog and removed changelog entries ..."
echo "=================================================================="
git add CHANGELOG.md
#git rm -r changelog.d
git commit -m "Add changelog for release $1"
