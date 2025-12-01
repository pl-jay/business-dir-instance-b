
#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   ./sync.sh                -> uses current working dir as DEV_DIR
#   ./sync.sh --dev-dir /abs/path/to/dev
#   ./sync.sh --dry-run
#   ./sync.sh --dev-dir /abs/path --dry-run

DRY_RUN=false
OVERRIDE_DEV_DIR=""
# parse args
while [ $# -gt 0 ]; do
  case "$1" in
    --dry-run) DRY_RUN=true; shift ;;
    --dev-dir) OVERRIDE_DEV_DIR="$2"; shift 2 ;;
    --help) echo "Usage: $0 [--dev-dir PATH] [--dry-run]"; exit 0 ;;
    *) echo "Unknown arg: $1"; exit 1 ;;
  esac
done

# DEFAULT: use the directory where the command is run (current working dir)
if [ -n "$OVERRIDE_DEV_DIR" ]; then
  DEV_DIR="$(cd "$OVERRIDE_DEV_DIR" && pwd)"
else
  DEV_DIR="$(pwd)"
fi

# INSTANCES: change these to your instance repo paths
INSTANCES=( "../business-dir-instance-a" "../business-dir-instance-b" )


# Always exclude .git and other instance-only paths
EXCLUDES=( --exclude='.git' --exclude='themes/*' --exclude='instance.env' --exclude='node_modules' --exclude='.venv' )

TAG="sync-$(date +%Y%m%d%H%M%S)"
GIT_USER_NAME="pl-jay"
GIT_USER_EMAIL="lakshan.jap@gmail.com"

echo "DEV_DIR: $DEV_DIR"
echo "DRY_RUN: $DRY_RUN"
echo "TAG: $TAG"
echo

for DST in "${INSTANCES[@]}"; do
  echo ">>> Processing $DST"

  # show absolute paths for clarity
  DST_ABS="$(cd "$(dirname "$DST")" && echo "$(pwd)/$(basename "$DST")")" || DST_ABS="$DST"
  echo "Instance path (raw): $DST"
  echo "Instance path (abs): $DST_ABS"

  # sanity checks
  if [ ! -e "$DST" ]; then
    echo "ERROR: $DST does not exist. Skipping."
    echo
    continue
  fi

  # reliable git check
  if ! git -C "$DST" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    echo "ERROR: $DST is not a git repo (git check failed). Skipping."
    echo
    continue
  fi

  # create + push backup branch BEFORE any changes
  pushd "$DST" >/dev/null
    git config user.name "$GIT_USER_NAME"
    git config user.email "$GIT_USER_EMAIL"
    git fetch --all --prune || true
    git checkout -B "pre-sync-backup-$TAG"
    git commit --allow-empty -m "backup before sync $TAG" || true
    if [ "$DRY_RUN" = false ]; then
      git push -u origin "pre-sync-backup-$TAG" || echo "Warning: couldn't push backup branch"
    else
      echo "[DRY RUN] would push backup branch: pre-sync-backup-$TAG"
    fi

    # return to main or master
    if git rev-parse --verify --quiet refs/heads/main >/dev/null; then
      git checkout main
    elif git rev-parse --verify --quiet refs/heads/master >/dev/null; then
      git checkout master
    fi
  popd >/dev/null

  # STAGE dev files in TMP, making sure .git is excluded
  TMPDIR="$(mktemp -d)"
  rsync -a "${EXCLUDES[@]}" "$DEV_DIR/" "$TMPDIR/"

  # show what would be copied (helpful)
  echo "Files staged in tmpdir (sample):"
  find "$TMPDIR" -maxdepth 2 -type f | sed -n '1,20p'
  echo "..."

  # overlay into instance repo — protect .git by excluding it
  if [ "$DRY_RUN" = true ]; then
    echo "[DRY RUN] rsync -av --delete ${EXCLUDES[*]} \"$TMPDIR/\" \"$DST/\""
    rsync -av --delete --dry-run "${EXCLUDES[@]}" "$TMPDIR/" "$DST/"
  else
    rsync -av --delete "${EXCLUDES[@]}" "$TMPDIR/" "$DST/"
  fi

  rm -rf "$TMPDIR"

  # commit & push in instance repo
  pushd "$DST" >/dev/null
    git add -A
    if git diff --cached --quiet; then
      echo "No changes to commit for $DST"
    else
      if [ "$DRY_RUN" = true ]; then
        echo "[DRY RUN] Would commit and push changes for $DST"
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
