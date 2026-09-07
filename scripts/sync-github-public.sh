#!/usr/bin/env bash
# Sync ~/Documents/github-public/ into the public repo's github-public/
# folder and push. This is the "mapping" — run it any time you drop files
# into the staging directory.
#
# Usage: sync-github-public.sh [--no-push]
set -euo pipefail

STAGE="$HOME/Documents/github-public"
REPO="$HOME/public"
DEST="$REPO/github-public"
BRANCH="wip"

[[ -d "$STAGE" ]] || { echo "staging dir missing: $STAGE" >&2; exit 1; }

cd "$REPO"
git fetch origin "$BRANCH" -q
git checkout "$BRANCH" -q 2>/dev/null || git checkout -b "$BRANCH" "origin/$BRANCH"
git pull --ff-only -q origin "$BRANCH"

mkdir -p "$DEST"
# Mirror staging into the repo folder (deletions included), but never
# clobber the README that documents the mapping.
rsync -a --delete --exclude='.git' --filter='protect README.md' \
  "$STAGE"/ "$DEST"/

if [[ -n "$(git status --porcelain -- "$DEST")" ]]; then
  git add "$DEST"
  git -c user.name="markneustadt" -c user.email="markneustadt@users.noreply.github.com" \
    commit -q -m "Sync github-public staging folder"
  if [[ "${1:-}" == "--no-push" ]]; then
    echo "committed (not pushed)"
  else
    git push -q origin "$BRANCH"
    echo "synced and pushed to origin/$BRANCH"
  fi
else
  echo "no changes"
fi
