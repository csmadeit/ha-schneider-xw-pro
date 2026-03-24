#!/usr/bin/env bash
# ============================================================================
# release.sh — Create a GitHub release for ha-schneider-xw-pro
#
# IMPORTANT: GitHub fine-grained PATs ignore "draft": false on POST.
# This script ALWAYS patches the release after creation to force non-draft.
# ============================================================================
set -euo pipefail

REPO="csmadeit/ha-schneider-xw-pro"
API="https://api.github.com/repos/$REPO/releases"

# ---------------------------------------------------------------------------
# 1. Resolve the GitHub PAT
# ---------------------------------------------------------------------------
if [[ -z "${GITHUB_PAT:-}" ]]; then
  echo "ERROR: GITHUB_PAT environment variable is not set."
  echo "Export it before running:  export GITHUB_PAT=github_pat_..."
  exit 1
fi

# ---------------------------------------------------------------------------
# 2. Read version from manifest.json
# ---------------------------------------------------------------------------
MANIFEST="custom_components/schneider_xw_pro/manifest.json"
if [[ ! -f "$MANIFEST" ]]; then
  echo "ERROR: $MANIFEST not found. Run this script from the repo root."
  exit 1
fi

VERSION=$(python3 -c "import json; print(json.load(open('$MANIFEST'))['version'])")
TAG="v$VERSION"
echo "Version from manifest.json: $VERSION  (tag: $TAG)"

# ---------------------------------------------------------------------------
# 3. Accept release title & body (or use defaults)
# ---------------------------------------------------------------------------
TITLE="${1:-$TAG}"
BODY="${2:-Release $TAG}"

# ---------------------------------------------------------------------------
# 4. Create the release (will likely be draft despite draft:false)
# ---------------------------------------------------------------------------
echo ""
echo "Creating GitHub release $TAG ..."
CREATE_RESPONSE=$(curl -s -X POST "$API" \
  -H "Authorization: Bearer $GITHUB_PAT" \
  -H "Accept: application/vnd.github+json" \
  -d "$(python3 -c "
import json, sys
print(json.dumps({
    'tag_name': '$TAG',
    'target_commitish': 'main',
    'name': '$TITLE',
    'body': '''$BODY''',
    'draft': False,
    'prerelease': False
}))
")")

RELEASE_ID=$(echo "$CREATE_RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin).get('id',''))" 2>/dev/null || true)

if [[ -z "$RELEASE_ID" ]]; then
  echo "ERROR: Failed to create release. Response:"
  echo "$CREATE_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$CREATE_RESPONSE"
  exit 1
fi

echo "Release created (id=$RELEASE_ID). Now forcing non-draft via PATCH..."

# ---------------------------------------------------------------------------
# 5. PATCH to force draft=false, then VERIFY with a separate GET.
#    Fine-grained PATs: PATCH response may claim draft=False but the
#    release can revert to draft. We loop up to 5 times, each time
#    PATCHing then sleeping and GETting to confirm.
# ---------------------------------------------------------------------------
MAX_ATTEMPTS=5
for attempt in $(seq 1 $MAX_ATTEMPTS); do
  echo "  Attempt $attempt/$MAX_ATTEMPTS: PATCH draft=false ..."
  curl -s -X PATCH "$API/$RELEASE_ID" \
    -H "Authorization: Bearer $GITHUB_PAT" \
    -H "Accept: application/vnd.github+json" \
    -d '{"draft": false}' > /dev/null

  sleep 3

  # Verify with a fresh GET (using release ID, NOT tag — tags 404 for drafts)
  DRAFT_STATUS=$(curl -s "$API/$RELEASE_ID" \
    -H "Authorization: Bearer $GITHUB_PAT" \
    -H "Accept: application/vnd.github+json" \
    | python3 -c "import sys,json; print(json.load(sys.stdin).get('draft','unknown'))" 2>/dev/null || true)

  echo "  GET verification: draft=$DRAFT_STATUS"

  if [[ "$DRAFT_STATUS" == "False" ]]; then
    echo "Release $TAG published successfully (draft=False, verified via GET)."
    echo "URL: https://github.com/$REPO/releases/tag/$TAG"
    break
  fi

  if [[ $attempt -eq $MAX_ATTEMPTS ]]; then
    echo "ERROR: Release $TAG is STILL draft=$DRAFT_STATUS after $MAX_ATTEMPTS attempts!"
    echo "Manually un-draft at: https://github.com/$REPO/releases/edit/$TAG"
    exit 1
  fi
done

# ---------------------------------------------------------------------------
# 6. Sync release branch (GitHub default branch is 'release', not 'main')
#    HACS downloads from the default branch — if release is behind, HACS
#    gets stale code even though the tag/release is correct.
# ---------------------------------------------------------------------------
echo ""
echo "Syncing main → release branch on GitHub..."
git push github main:release 2>/dev/null && echo "  release branch updated." || echo "  WARNING: Could not push to release branch (not fatal)."

# ---------------------------------------------------------------------------
# 7. Final verification — re-read from API using release ID (not tag)
# ---------------------------------------------------------------------------
echo ""
echo "Final verification (using release ID $RELEASE_ID)..."
VERIFY=$(curl -s "$API/$RELEASE_ID" \
  -H "Authorization: Bearer $GITHUB_PAT" \
  -H "Accept: application/vnd.github+json" | python3 -c "import sys,json; r=json.load(sys.stdin); print(f'  tag={r[\"tag_name\"]} draft={r[\"draft\"]} url={r[\"html_url\"]}')" 2>/dev/null || true)
echo "$VERIFY"
echo ""
echo "Done. HACS should see $TAG."
