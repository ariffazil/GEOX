#!/bin/sh
# FAIL-CLOSED RAIL (FI-003 2026-10-30; revised 2026-11-24 by ARIF).
# Blocks a push if any commit BEING PUSHED touches a sensitive path.
# Old version scanned --all local refs (false blocks); kept as pre-push.bak-20261124-allrefs.
# If this hook errors, that is a STOP, not a warning.
set -u
PATTERN='^\.archive/|^\.megamemory/|(^|/)(media|cache)/|\.db(-wal|-shm)?$'
fail=0
while read -r lref lsha rref rsha; do
  case "$lsha" in *[!0]*) ;; *) continue ;; esac
  case "$rsha" in *[!0]*) range="$rsha..$lsha" ;; *) range="$lsha --not --remotes" ;; esac
  out=$(git log --name-only --pretty=format: $range 2>&1) || { echo "PRE-PUSH BLOCKED: cannot scan $range"; exit 1; }
  hits=$(printf '%s\n' "$out" | grep -cE "$PATTERN" || true)
  if [ "${hits:-1}" -gt 0 ]; then
    echo "PRE-PUSH BLOCKED: $hits sensitive path-occurrence(s) in commits being pushed to $rref"
    printf '%s\n' "$out" | grep -E "$PATTERN" | sort -u | head -10
    fail=1
  fi
done
exit $fail
