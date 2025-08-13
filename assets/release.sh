#!/usr/bin/env sh

tag_content="$(towncrier build --draft | grep -A 1000 '^###')"

echo "=================================================================="
towncrier build --yes

echo ""
echo "=================================================================="
echo "Updating the CHANGELOG.md and committing it to the current branch."
echo "=================================================================="
git add CHANGELOG.md
git stage changelog.d/**.md
git commit -m "Adding changelog for Release $1"

echo "=================================================================="
echo "Creating an annotated tag with this message:"
echo "=================================================================="
echo "$tag_content"
echo "=================================================================="

echo "=================================================================="
echo "Generating the release:"
echo "=================================================================="
echo "$tag_content" > "tmp-$1.md"
gh release create "$1" --title "Release $1" --notes-file "tmp-$1.md"
rm "tmp-$1.md"

echo "=================================================================="
echo "Pushing the changelog commit:"
echo "=================================================================="
git push
