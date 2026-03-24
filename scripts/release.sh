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
# 5. PATCH to force draft=false (the CRITICAL step)
# ---------------------------------------------------------------------------
PATCH_RESPONSE=$(curl -s -X PATCH "$API/$RELEASE_ID" \
  -H "Authorization: Bearer $GITHUB_PAT" \
  -H "Accept: application/vnd.github+json" \
  -d '{"draft": false}')

DRAFT_STATUS=$(echo "$PATCH_RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin).get('draft','unknown'))" 2>/dev/null || true)

if [[ "$DRAFT_STATUS" == "False" ]]; then
  echo "Release $TAG published successfully (draft=False)."
  echo "URL: https://github.com/$REPO/releases/tag/$TAG"
else
  echo "WARNING: PATCH returned draft=$DRAFT_STATUS. Retrying..."
  sleep 2
  RETRY_RESPONSE=$(curl -s -X PATCH "$API/$RELEASE_ID" \
    -H "Authorization: Bearer $GITHUB_PAT" \
    -H "Accept: application/vnd.github+json" \
    -d '{"draft": false}')
  DRAFT_STATUS=$(echo "$RETRY_RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin).get('draft','unknown'))" 2>/dev/null || true)
  if [[ "$DRAFT_STATUS" == "False" ]]; then
    echo "Release $TAG published successfully after retry (draft=False)."
    echo "URL: https://github.com/$REPO/releases/tag/$TAG"
  else
    echo "ERROR: Release $TAG is STILL draft=$DRAFT_STATUS after retry!"
    echo "Manually un-draft at: https://github.com/$REPO/releases/edit/$TAG"
    exit 1
  fi
fi

# ---------------------------------------------------------------------------
# 6. Final verification — re-read from API to confirm
# ---------------------------------------------------------------------------
echo ""
echo "Verifying..."
VERIFY=$(curl -s "$API/tags/$TAG" \
  -H "Authorization: Bearer $GITHUB_PAT" \
  -H "Accept: application/vnd.github+json" | python3 -c "import sys,json; r=json.load(sys.stdin); print(f'  tag={r[\"tag_name\"]} draft={r[\"draft\"]} url={r[\"html_url\"]}')" 2>/dev/null || true)
echo "$VERIFY"
echo ""
echo "Done. HACS should see $TAG."
