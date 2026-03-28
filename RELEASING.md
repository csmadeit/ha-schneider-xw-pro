# Release Process

## Overview

This integration is developed on **GitLab** (primary) and mirrored to **GitHub** for HACS distribution.

- **GitLab (primary):** https://gitlab.cmhtransfer.com/independent/ha-schneider-xw-pro
- **GitHub (HACS mirror):** https://github.com/csmadeit/ha-schneider-xw-pro
- **HACS default branch:** `release` (on GitHub)

## CRITICAL: Version Alignment Rules

**The `version` field in `manifest.json` MUST always match the GitHub release tag.**

HACS compares the installed version (from `manifest.json`) against the latest GitHub release tag.
If `manifest.json` has a higher version than the release tag, HACS will never show an update.

**Before every release:**
1. Update `version` in `custom_components/schneider_xw_pro/manifest.json` to the new version
2. Commit and merge that change
3. Create a git tag with the SAME version (prefixed with `v`)
4. Create a GitHub release from that tag

**Example:** To release version `2.1.0`:
- `manifest.json` must say `"version": "2.1.0"`
- Git tag must be `v2.1.0`
- GitHub release must be tagged `v2.1.0`

**Never** create a GitHub release tag that is lower than the `manifest.json` version.

## How to Release a New Version

### 1. Make changes on GitLab

All development happens on GitLab. Create a branch, make changes, create an MR, and merge to `main`.

**Important:** Before merging the final MR, ensure `manifest.json` version is bumped to the new release version.

### 2. Sync to GitHub

After merging to `main` on GitLab, push to GitHub:

```bash
# From the repo directory
git checkout main
git pull origin main

# Push to both GitHub branches
git push github main
git push github main:release
```

### 3. Create a version tag

```bash
# IMPORTANT: Version in tag MUST match version in manifest.json
# Verify first:
grep '"version"' custom_components/schneider_xw_pro/manifest.json

# Create annotated tag (must match manifest.json version)
git tag -a vX.Y.Z -m "vX.Y.Z: Brief description of changes"

# Push tag to both remotes
git push origin vX.Y.Z
git push github vX.Y.Z
```

### 4. Create GitHub Release

**ALWAYS use the release script** to avoid the draft release bug:

```bash
export GITHUB_PAT="github_pat_..."
./scripts/release.sh "vX.Y.Z: Title" "Release notes here"
```

The script reads the version from `manifest.json`, creates the release, and
automatically PATCHes it to non-draft with verification.

> **WARNING — DRAFT RELEASE BUG:** GitHub fine-grained PATs silently ignore
> `"draft": false` on `POST /releases`. The release is ALWAYS created as a
> draft. The ONLY fix is to follow the POST with a `PATCH` that sets
> `{"draft": false}`. The `scripts/release.sh` script handles this
> automatically. **NEVER create releases manually via the API without the
> PATCH step — HACS cannot see draft releases.**

### 5. HACS picks up the release

HACS automatically detects new GitHub releases. Users will see the update in HACS.

## Version History

| Version | Date | Description |
|---------|------|-------------|
| v0.1.0 | 2026-03-14 | Initial release with basic Modbus read/write |
| v1.0.0 | 2026-03-22 | Initial release — pyModbusTCP, discovery, basic registers |
| v1.1.0 | 2026-03-22 | Complete register coverage (281 registers from official Schneider specs) |
| v1.2.0 | 2026-03-22 | Temperature handling, charger/inverter status enums, clean release history |
| v1.3.0 | 2026-03-22 | Retry logic for grayed-out status entities |
| v1.3.1 | 2026-03-22 | Block reads to reduce TCP connections from 117 to ~14 |
| v1.3.2 | 2026-03-24 | Fix entity name duplication, reduce block size to 50, WARNING diagnostics |
| v1.3.3 | 2026-03-24 | Fix MPPT block read failures (ILLEGAL_DATA_ADDRESS), max_gap=1 |
| v1.3.4 | 2026-03-24 | Fix status entities — reduce max_gap from 3 to 1 |
| v1.3.5 | 2026-03-24 | Fix entity registration errors (None entity names, duplicate keys) |
| v1.3.6 | 2026-03-24 | Add units/device_class to Apparent Power sensors (VA) |
| v1.3.7 | 2026-03-28 | Fix PV Power/Current: sensor registers from HOLDING to INPUT (FC 0x04) |

## HACS Custom Repository Setup (for users)

1. Open HACS in Home Assistant
2. Go to **Integrations** > three-dot menu > **Custom repositories**
3. Add URL: `https://github.com/csmadeit/ha-schneider-xw-pro`
4. Category: **Integration**
5. Click **Add**
6. Install **Schneider Electric Conext XW Pro**
7. Restart Home Assistant

## HACS Official Listing (future)

To get listed in the official HACS default repository:
1. Ensure all [HACS requirements](https://hacs.xyz/docs/publish/integration) are met
2. Submit a PR to https://github.com/hacs/default adding the repo
3. Requirements include: hacs.json, proper manifest.json, GitHub releases, README

## Git Remote Setup

```bash
# GitLab (origin) - already configured
git remote add origin https://gitlab.cmhtransfer.com/independent/ha-schneider-xw-pro.git

# GitHub (for HACS) - add manually
git remote add github https://github.com/csmadeit/ha-schneider-xw-pro.git
```
