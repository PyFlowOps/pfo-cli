#!/usr/bin/env bash

# We want to make some change to the code, but keep the same tag for the version
RELEASE_TAG="v0.0.2"

git tag --delete "${RELEASE_TAG}"
git push --delete origin "${RELEASE_TAG}"

# Now we can push the new tag
git tag -a "${RELEASE_TAG}" -m "Release: ${RELEASE_TAG} -- SRE Automated Release/Tagging"
git push origin "${RELEASE_TAG}"
