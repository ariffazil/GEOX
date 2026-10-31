#!/bin/sh
# FAIL-CLOSED RAIL (FI-003 2026-10-30, corak CHRON) — blocks any push from THIS raw repo.
# Box GEOX is raw; sanctioned remote history filtered in /root/geox-push-mirror.
# If this hook errors, that is a STOP, not a warning.
set -u
REPO="$(git rev-parse --git-dir 2>/dev/null || true)"
cd "$(dirname "$0")/.." || exit 1
PATTERN='^\.archive/|^\.megamemory/|(^|/)(media|cache)/|\.db(-wal|-shm)?$'
hits=$(git log --all --name-only --pretty=format: 2>/dev/null | grep -cE "$PATTERN")
[ -z "${REPO:-}" ] && { echo "PRE-PUSH BLOCKED: no git dir"; exit 1; }
if [ "${hits:-1}" -gt 0 ]; then
  echo "PRE-PUSH BLOCKED: $hits sensitive path-occurrence(s) in raw history."
  echo "Push from the filtered mirror instead: /root/geox-push-mirror (re-filter after new commits)"
  exit 1
fi
