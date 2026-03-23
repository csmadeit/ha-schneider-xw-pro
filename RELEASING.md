# Release Process

## Overview

This integration is developed on **GitLab** (primary) and mirrored to **GitHub** for HACS distribution.

- **GitLab (primary):** https://gitlab.cmhtransfer.com/independent/ha-schneider-xw-pro
- **GitHub (HACS mirror):** https://github.com/csmadeit/ha-schneider-xw-pro
- **HACS default branch:** `release` (on GitHub)

## How to Release a New Version

### 1. Make changes on GitLab

All development happens on GitLab. Create a branch, make changes, create an MR, and merge to `main`.

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
# Create annotated tag
git tag -a v0.X.Y -m "v0.X.Y: Brief description of changes"

# Push tag to both remotes
git push origin v0.X.Y
git push github v0.X.Y
```

### 4. Create GitHub Release

Go to https://github.com/csmadeit/ha-schneider-xw-pro/releases/new or use the API:

```bash
curl -X POST -H "Authorization: token \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"   -H "Accept: application/vnd.github.v3+json"   "https://api.github.com/repos/csmadeit/ha-schneider-xw-pro/releases"   -d '{
    "tag_name": "v0.X.Y",
    "target_commitish": "release",
    "name": "v0.X.Y: Title",
    "body": "Release notes here",
    "draft": false,
    "prerelease": false
  }'
```

### 5. HACS picks up the release

HACS automatically detects new GitHub releases. Users will see the update in HACS.

## Version History

| Version | Date | Description |
|---------|------|-------------|
| v0.1.0 | 2026-03-14 | Initial release with basic Modbus read/write |
| v0.2.0 | 2026-03-22 | Register rewrite from official Schneider specs + device auto-discovery |

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
