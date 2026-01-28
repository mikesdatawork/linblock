# LinBlock Release Procedure

Version: 1.0.0
Status: Draft
Last Updated: 2025-01-28
Owner: Agent 010 (DevOps)

---

## 1. Overview

This document defines the release procedure for the LinBlock project. It covers versioning strategy, branch conventions, release workflow, and the complete release checklist.

---

## 2. Semantic Versioning

LinBlock uses [Semantic Versioning 2.0.0](https://semver.org/):

```
MAJOR.MINOR.PATCH
```

### 2.1 Version Increment Rules

| Change Type            | Version Bump | Example       | Description                              |
|------------------------|--------------|---------------|------------------------------------------|
| Breaking API change    | MAJOR        | 1.0.0 -> 2.0.0 | Incompatible changes to module interfaces |
| New feature            | MINOR        | 1.0.0 -> 1.1.0 | Backward-compatible feature additions     |
| Bug fix                | PATCH        | 1.0.0 -> 1.0.1 | Backward-compatible bug fixes             |
| Pre-release            | Suffix       | 1.0.0-alpha.1  | Development/testing versions              |

### 2.2 Version Locations

The version string is maintained in these files:

| File                   | Format                         |
|------------------------|--------------------------------|
| `pyproject.toml`       | `version = "X.Y.Z"`           |
| `src/__init__.py`      | `__version__ = "X.Y.Z"`       |
| `CHANGELOG.md`         | `## [X.Y.Z] - YYYY-MM-DD`     |

All version locations MUST be updated together. Use the version bump script:

```bash
python scripts/bump_version.py {major|minor|patch}
```

### 2.3 Initial Versioning

The project starts at `0.1.0`. The `0.x.y` series indicates pre-1.0 development where the API is not yet stable:

- `0.1.0` -- Phase A complete (architecture, module stubs, CI)
- `0.2.0` -- Phase B complete (infrastructure modules implemented)
- `0.3.0` -- Phase C complete (emulation core working)
- `0.x.0` -- Subsequent phases
- `1.0.0` -- First stable public release

---

## 3. Branch Conventions

### 3.1 Branch Model

LinBlock uses a simplified Git Flow branching model:

```
main ─────────────────────────────────────────────> (stable releases)
  \                    \              /
   develop ─────────────────────────────────────> (integration)
     \       \       /     \       /
      feature/x    feature/y    feature/z        (work branches)
```

### 3.2 Branch Types

| Branch         | Purpose                        | Created From | Merges Into    | Lifetime    |
|----------------|--------------------------------|--------------|----------------|-------------|
| `main`         | Stable, released code          | --           | --             | Permanent   |
| `develop`      | Integration branch             | `main`       | `main`         | Permanent   |
| `feature/*`    | New feature development        | `develop`    | `develop`      | Temporary   |
| `bugfix/*`     | Bug fix development            | `develop`    | `develop`      | Temporary   |
| `hotfix/*`     | Critical production fix        | `main`       | `main` + `develop` | Temporary |
| `release/*`    | Release preparation            | `develop`    | `main` + `develop` | Temporary |

### 3.3 Branch Naming Convention

```
feature/{module-name}/{short-description}
bugfix/{issue-number}-{short-description}
hotfix/{issue-number}-{short-description}
release/v{MAJOR}.{MINOR}.{PATCH}
```

**Examples:**
```
feature/config-manager/add-yaml-support
bugfix/42-fix-event-bus-deadlock
hotfix/99-security-patch-sandbox
release/v0.1.0
```

### 3.4 Branch Protection Rules

| Branch    | Required Reviews | CI Must Pass | Force Push | Delete After Merge |
|-----------|------------------|--------------|------------|-------------------|
| `main`    | 2                | Yes          | Never      | N/A               |
| `develop` | 1                | Yes          | Never      | N/A               |
| `feature/*` | 1              | Yes          | Allowed    | Yes               |

---

## 4. Tag Format

### 4.1 Release Tags

Release tags are annotated Git tags following the format:

```
v{MAJOR}.{MINOR}.{PATCH}
```

**Examples:**
```
v0.1.0
v0.2.0
v1.0.0
v1.0.1
```

### 4.2 Pre-release Tags

```
v{MAJOR}.{MINOR}.{PATCH}-{stage}.{number}
```

Where `{stage}` is one of: `alpha`, `beta`, `rc`

**Examples:**
```
v0.1.0-alpha.1
v0.1.0-beta.1
v0.1.0-rc.1
v1.0.0-rc.2
```

### 4.3 Creating Tags

```bash
# Create annotated release tag
git tag -a v0.1.0 -m "Release v0.1.0: Phase A complete"

# Push tag to remote
git push origin v0.1.0
```

---

## 5. Changelog Generation

### 5.1 Changelog Structure

The project maintains a root `CHANGELOG.md` that aggregates changes from all modules.

**Root CHANGELOG.md format:**

```markdown
# Changelog

All notable changes to LinBlock are documented in this file.
Format follows [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

### Added
- ...

### Changed
- ...

### Fixed
- ...

## [0.1.0] - 2025-01-28

### Added
- Initial project architecture
- Module template and generator
- CI pipeline with lint and test stages
- ...
```

### 5.2 Module-Level Changelogs

Each module maintains its own `CHANGELOG.md` within its directory:

```
src/modules/{layer}/{module_name}/CHANGELOG.md
```

Module changelogs follow the same format but are scoped to that module's changes.

### 5.3 Changelog Generation Process

1. Before each release, module owners update their module `CHANGELOG.md`
2. The release manager aggregates module changelogs into the root `CHANGELOG.md`
3. The aggregation script automates this:

```bash
python scripts/generate_changelog.py --version 0.1.0
```

This script:
- Reads each module's `CHANGELOG.md` `[Unreleased]` section
- Prefixes each entry with `[module_name]`
- Combines into the root changelog under the new version heading
- Moves entries from `[Unreleased]` to the version section

### 5.4 Changelog Entry Guidelines

- Use present tense: "Add feature" not "Added feature"
- Start with a verb: Add, Fix, Update, Remove, Deprecate
- Reference issue numbers when applicable: `Fix event bus race condition (#42)`
- Categorize entries: Added, Changed, Deprecated, Removed, Fixed, Security

---

## 6. Release Workflow

### 6.1 Release Process Overview

```
1. Create release branch
2. Version bump
3. Update changelogs
4. Run full test suite
5. Build artifacts
6. Create PR to main
7. Review and approve
8. Merge to main
9. Tag release
10. Create GitHub Release
11. Merge back to develop
12. Announce release
```

### 6.2 Detailed Steps

#### Step 1: Create Release Branch

```bash
git checkout develop
git pull origin develop
git checkout -b release/v0.1.0
```

#### Step 2: Version Bump

```bash
# Bump version in all locations
python scripts/bump_version.py minor  # or major/patch

# Verify version consistency
python scripts/check_version.py
```

#### Step 3: Update Changelogs

```bash
# Generate aggregated changelog
python scripts/generate_changelog.py --version 0.1.0

# Review and edit the generated changelog
# Ensure all notable changes are documented
```

#### Step 4: Run Full Test Suite

```bash
# Unit tests with coverage
pytest tests/unit/ --cov=src --cov-report=term-missing -v

# Integration tests
pytest tests/integration/ -v

# Performance benchmarks
pytest tests/performance/ -v -m performance

# Security tests
pytest tests/security/ -v

# Lint and type check
flake8 src/ tests/
mypy src/

# 4-hour stability test (for major/minor releases)
python scripts/stability_test.py --duration 4h
```

#### Step 5: Build Artifacts

```bash
# Build application bundle
python scripts/build.py --release

# Build system images (if changed)
python scripts/build_aosp.py --arch x86_64

# Generate checksums
sha256sum dist/linblock-*.tar.gz > dist/SHA256SUMS.txt
```

#### Step 6: Create PR to Main

```bash
git add -A
git commit -m "Release v0.1.0"
git push origin release/v0.1.0
gh pr create --base main --title "Release v0.1.0" --body "Release v0.1.0 - see CHANGELOG.md"
```

#### Step 7: Review and Approve

- At least 2 reviewers must approve
- All CI checks must pass
- Changelog must be reviewed for accuracy

#### Step 8: Merge to Main

```bash
# Merge via GitHub PR (no fast-forward)
gh pr merge --merge
```

#### Step 9: Tag Release

```bash
git checkout main
git pull origin main
git tag -a v0.1.0 -m "Release v0.1.0"
git push origin v0.1.0
```

#### Step 10: Create GitHub Release

```bash
gh release create v0.1.0 \
    dist/linblock-0.1.0-*.tar.gz \
    dist/SHA256SUMS.txt \
    --title "LinBlock v0.1.0" \
    --notes-file CHANGELOG_RELEASE.md
```

#### Step 11: Merge Back to Develop

```bash
git checkout develop
git merge main
git push origin develop
```

#### Step 12: Announce Release

- Post to project communication channels
- Update project documentation site
- Notify downstream dependents

---

## 7. Release Checklist

### 7.1 Pre-Release Checklist

Use this checklist before every release. All items must be completed.

```
[ ] Version bumped in pyproject.toml
[ ] Version bumped in src/__init__.py
[ ] CHANGELOG.md updated with all changes
[ ] Module CHANGELOGs updated by module owners
[ ] All unit tests pass (0 failures)
[ ] Code coverage >= 70% per module
[ ] All integration tests pass (0 failures)
[ ] Performance benchmarks within acceptable limits
[ ] Security tests pass (0 failures)
[ ] Lint passes (flake8 returns 0)
[ ] Type check passes (mypy returns 0)
[ ] 4-hour stability test passes (major/minor releases)
[ ] Documentation updated to match implementation
[ ] API docs reflect current interfaces
[ ] No critical or high-severity open issues
[ ] Release branch PR created and approved
[ ] Artifacts built and checksums generated
```

### 7.2 Post-Release Checklist

```
[ ] Release tag created and pushed
[ ] GitHub Release created with artifacts
[ ] Release branch merged to main
[ ] Main merged back to develop
[ ] Release branch deleted
[ ] Release announcement posted
[ ] Package registry updated (if applicable)
[ ] Nightly build config updated for next version
```

---

## 8. Hotfix Procedure

For critical bugs found in production releases:

### 8.1 Hotfix Workflow

```bash
# 1. Create hotfix branch from main
git checkout main
git checkout -b hotfix/99-critical-fix

# 2. Apply fix
# ... make changes ...

# 3. Bump patch version
python scripts/bump_version.py patch

# 4. Update changelog
# Add entry under new version

# 5. Run tests
pytest tests/unit/ -v
pytest tests/integration/ -v

# 6. Create PR to main
git push origin hotfix/99-critical-fix
gh pr create --base main --title "Hotfix v1.0.1: Critical fix description"

# 7. After merge, tag and release
git checkout main && git pull
git tag -a v1.0.1 -m "Hotfix v1.0.1"
git push origin v1.0.1

# 8. Merge back to develop
git checkout develop
git merge main
git push origin develop
```

---

## 9. Rollback Procedure

If a release is found to be critically broken after deployment:

### 9.1 Steps

1. Identify the last known good release tag
2. Communicate the rollback to all stakeholders
3. Point users to the previous release artifacts
4. Create a hotfix branch to address the issue
5. Follow the hotfix procedure for the corrected release

### 9.2 GitHub Release Rollback

```bash
# Mark the broken release as pre-release (not latest)
gh release edit v1.1.0 --prerelease

# Ensure previous stable release is marked as latest
gh release edit v1.0.1 --latest
```

---

## 10. References

- Semantic Versioning: https://semver.org/
- Keep a Changelog: https://keepachangelog.com/
- LinBlock Artifact Storage: `docs/design/artifact_storage.md`
- LinBlock CI Pipeline: `.github/workflows/ci.yml`
- LinBlock Test Strategy: `docs/design/test_strategy.md`
