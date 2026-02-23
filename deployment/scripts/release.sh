#!/bin/bash
set -euo pipefail

if [ -z "${1:-}" ]; then
  echo "Usage: ./scripts/release.sh vX.Y.Z"
  exit 1
fi

TAG="$1"

if [[ ! "$TAG" =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
  echo "Invalid tag format. Use vX.Y.Z"
  exit 1
fi

git fetch --tags

if git rev-parse "$TAG" >/dev/null 2>&1; then
  echo "Tag $TAG already exists"
  exit 1
fi

echo "Creating tag $TAG"
git tag "$TAG"

echo "Pushing tag $TAG"
git push origin "$TAG"
