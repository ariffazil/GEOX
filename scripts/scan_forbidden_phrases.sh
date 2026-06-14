#!/bin/bash
# GEOX Claim Grammar Scanner — Forbidden Phrase Detector
# Scans GEOX MCP tool descriptions, docs, and test outputs for forbidden
# geological phrases that overclaim without evidence chains.
#
# Part of Merge Gatekeeper G5.
# DITEMPA BUKAN DIBERI

set -e

TARGET_DIR="${1:-/root/geox/src}"
EXIT_CODE=0

FORBIDDEN_PHRASES=(
    "proven reservoir"
    "confirmed hydrocarbon"
    "proven shoreface"
    "100% confidence"
    "definitely"
    "proved up"
    "de-risked"
    "guaranteed"
    "no risk"
    "certain,"
    "certain."
)

echo "=== GEOX Claim Grammar Scan ==="
echo "Scanning $TARGET_DIR for forbidden phrases..."
echo ""

for phrase in "${FORBIDDEN_PHRASES[@]}"; do
    matches=$(grep -rn --include="*.py" --include="*.ts" --include="*.tsx" --include="*.md" \
        -i "$phrase" "$TARGET_DIR" 2>/dev/null \
        | grep -v "node_modules" | grep -v ".pyc" | grep -v "__pycache__" \
        | grep -vi "uncertain" | grep -vi "certainty" | grep -vi "certainly" \
        | grep -vi "claim_too_certain" | grep -vi "anti_beautiful" \
        | grep -vi "SEGY_Rev\|rev_1\|rev_2\|2.0\|3.0" || true)
    if [ -n "$matches" ]; then
        echo "❌ FORBIDDEN PHRASE FOUND: '$phrase'"
        echo "$matches"
        echo ""
        EXIT_CODE=1
    fi
done

# Also scan for "bright spot" without evidence context
bright_spot_matches=$(grep -rn --include="*.py" --include="*.ts" --include="*.tsx" \
    -i "bright.spot" "$TARGET_DIR" 2>/dev/null | grep -v "node_modules" | grep -v ".pyc" || true)
if [ -n "$bright_spot_matches" ]; then
    echo "⚠️  POTENTIAL CLAIM GRAMMAR: 'bright spot' found — ensure AVO context"
    echo "$bright_spot_matches"
    echo ""
fi

if [ "$EXIT_CODE" -eq 0 ]; then
    echo "✅ No forbidden phrases found."
else
    echo "❌ CLAIM GRAMMAR VIOLATIONS DETECTED. Fix before merge."
fi

exit $EXIT_CODE
