#!/usr/bin/env bash
set -euo pipefail

# usage: ./sync.sh [--dry-run]
DRY_RUN=false
if [ "${1:-}" = "--dry-run" ]; then
  DRY_RUN=true
  echo "DRY RUN: no commits or pushes will be done"
fi

# CONFIG - change these to your real paths
DEV_DIR="$(cd "$(dirname "$0")/.." && pwd)"  # repo root (main dev)
INSTANCE_REPOS=( "../business-dir-instance-a" "../business-dir-instance-b" )

EXCLUDES=(
  --exclude='.git'
  --exclude='themes/*'
  --exclude='instance.env'
  --exclude='deploy/*.secret'
  --exclude='node_modules'
)

TAG="sync-$(date +%Y%m%d%H%M%S)"
GIT_USER_NAME="pl-jay"
GIT_USER_EMAIL="lakshan.jap@gmail.com"

echo "DEV_DIR: $DEV_DIR"
echo "TAG: $TAG"
echo

# run tests/build in dev (uncomment)
# echo "Running tests..."
# (cd "$DEV_DIR" && ./scripts/run_tests.sh) || { echo "Tests failed — aborting"; exit 1; }

for DST in "${INSTANCE_REPOS[@]}"; do
  echo ">>> Processing $DST"

  if [ ! -d "$DST" ]; then
    echo "ERROR: $DST does not exist. Skipping."
    continue
  fi

  if [ ! -d "$DST/.git" ]; then
    echo "ERROR: $DST is not a git repo (no .git). Skipping."
    continue
  fi

  # 1) Create a backup branch inside the instance repo BEFORE syncing
  pushd "$DST" >/dev/null
    git config user.name "$GIT_USER_NAME"
    git config user.email "$GIT_USER_EMAIL"

    # create a lightweight backup branch at current HEAD
    git fetch --all --prune || true
    git checkout -B "pre-sync-backup-$TAG"
    git commit --allow-empty -m "backup before sync $TAG" || true
    # switch back to main (or master)
    if git show-ref --verify --quiet refs/heads/main; then
      git checkout main
    elif git show-ref --verify --quiet refs/heads/master; then
      git checkout master
    else
      # fallback to current HEAD if neither main/master exist
      echo "No main/master branch found; staying on current branch."
    fi
  popd >/dev/null

  # 2) Stage dev files in a temp dir (respecting EXCLUDES)
  TMPDIR="$(mktemp -d)"
  rsync -a "${EXCLUDES[@]}" "$DEV_DIR/" "$TMPDIR/"

  # 3) Sync staged files INTO the instance repo (use same EXCLUDES to protect .git)
  if [ "$DRY_RUN" = true ]; then
    echo "[DRY RUN] rsync -av --delete ${EXCLUDES[*]} \"$TMPDIR/\" \"$DST/\""
    rsync -av --delete --dry-run "${EXCLUDES[@]}" "$TMPDIR/" "$DST/"
  else
    rsync -av --delete "${EXCLUDES[@]}" "$TMPDIR/" "$DST/"
  fi

  rm -rf "$TMPDIR"

  # 4) Commit & push changes from inside the instance repo
  pushd "$DST" >/dev/null
    git add -A
    if git diff --cached --quiet; then
      echo "No changes to commit for $DST"
    else
      if [ "$DRY_RUN" = true ]; then
        echo "[DRY RUN] would commit and push changes for $DST"
      else
        git commit -m "chore(sync): $TAG - sync from dev repo"
        git push origin HEAD
        echo "Pushed sync to $DST"
      fi
    fi
  popd >/dev/null

  echo ">>> Done $DST"
  echo
done

echo "All done. Tag: $TAG"
