#!/usr/bin/env bash
# Run a plugin tree the way upstream CI does: a standalone checkout named hermes-xmpp-plugin,
# upstream's pinned requirements, `pytest tests/ -q -W error`. The dev project's own pytest
# config would otherwise hide failures (asyncio auto mode, different warning filters).
#
# usage: scripts/ci_like.sh <git-ref | WORKTREE> [extra pytest args]
#   needs /tmp/venv-3.14, /tmp/venv-3.13 (with requirements*.txt and requirements-calls.txt) and
#   /tmp/venv-bare (without requirements-calls.txt); see "Venvs" below to recreate them.
#
# Venvs, from a plugin checkout:
#   for v in 3.14 3.13; do uv venv --python $v /tmp/venv-$v && uv pip install --python /tmp/venv-$v/bin/python \
#     -r requirements.txt -r requirements-dev.txt -r requirements-calls.txt; done
#   uv venv --python 3.14 /tmp/venv-bare && uv pip install --python /tmp/venv-bare/bin/python \
#     -r requirements.txt -r requirements-dev.txt
set -u
ref=${1:?usage: ci_like.sh <git-ref|WORKTREE>}
shift
plugin=$(cd "$(dirname "$0")/../plugin" && pwd)
work=$(mktemp -d /tmp/ci-like.XXXXXX)
dest=$work/hermes-xmpp-plugin
mkdir -p "$dest"
if [ "$ref" = WORKTREE ]; then
  rsync -a --exclude .git --exclude __pycache__ "$plugin"/ "$dest"/
else
  git -C "$plugin" archive "$ref" | tar x -C "$dest"
fi
cd "$dest" || exit 1
for v in 3.14 3.13 bare; do
  py=/tmp/venv-$v/bin/python
  [ -x "$py" ] || { echo "== $ref $v: missing $py"; continue; }
  echo "== $ref ($v)"
  # CI sets this, so a missing call dependency fails instead of silently skipping the engine tests
  require=1; [ "$v" = bare ] && require=
  XMPP_REQUIRE_CALL_DEPS=$require timeout 600 "$py" -m pytest tests/ -q -W error -o asyncio_default_fixture_loop_scope=function -p no:cacheprovider "$@" 2>&1 \
    | grep -E "^FAILED|^ERROR|passed|failed" | sed 's/ - .*//'
done
echo "(checked out in $dest)"
