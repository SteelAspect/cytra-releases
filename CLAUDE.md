# Alloy Releases (repo: cytra-releases)

Public home of the Alloy mod jars, the update manifests that Alloy Hub reads, the download page, and `release.py`. Workspace rules: `../CLAUDE.md`. **This repo is public: write nothing private into it.** Never release, publish or edit the manifest without the user's OK.

## What it is
- GitHub `SteelAspect/cytra-releases`, branch `main`, served by GitHub Pages (`.nojekyll`): download page `index.html`, manifests `manifest.json` (Minecraft 1.21.11, 22 mod entries) and `manifest-1.20.4.json` (14 entries, read only by the 1.20.4 Hub) and `manifest-26.3.json` (read only by the 26.3 Hub), `alloy-logo.png`, `README.md`.
- Jars live in GitHub releases named `<id>-v<version>` (Alloy Pack: `alloypack-v<version>`, 13 zips; Cytra Link: `cytra-link-v<version>`); 1.20.4 releases are tagged with `+1.20.4`.

## Stack
- Python 3 and the `gh` CLI logged in with push access. No build system. `__pycache__` is ignored.

## Code map
- `release.py` (about 260 lines): `python release.py [--unlisted] [--replaces <old-id>] [--mc 1.20.4|26.3] <jar> "<changelog>"`. Reads id/name/version/environment/depends from `fabric.mod.json` in the jar, computes SHA-256, creates the GitHub release with the jar, updates the manifest entry (`id`, `name`, `version`, `url`, `sha256`, `changelog`, `environment`, `depends`, `optional`, `listed`, optional `replaces`/`renamedTo`/`minecraft`), commits and pushes, then adds the changelog to Alloy Hub's built-in list (`src/client/resources/cytra-hub/mods.json` in `../cytra-hub`, or `$CYTRA_HUB`) and commits it there without pushing. Refuses a version already in the manifest and a jar whose Minecraft doesn't match `--mc` (or a 1.20.4/26.x jar without it). Takes a file lock so two releases cannot run at once.
- `index.html`: reads the manifest for the chosen Minecraft version and lists mods that are `listed`.

## Build and test
- No tests. Dry check after a release: the live manifest shows the new version and the downloaded jar's SHA-256 matches (PROGRESS lines of the mod repos record this). Do not download jars unasked.

## Cross-mod links
- Alloy Hub (**hub** chat) reads `manifest.json` (Updates tab, install of missing mods, "This server uses"): keep the format backward compatible. A brand-new mod also needs a `put(...)` line in Hub's `ModCatalog.java` (the script reminds you). Every mod chat calls `release.py` for its own mod only after the user says release.

## Decisions and gotchas
- `--unlisted` marks a mod `listed:false` (Hub offers it only to players who already have it; the page hides it); the flag is kept on later releases. Unlisted today: cytramap, cytra-masscraft, cytrasend, cytra-link.
- `--replaces <old-id>`: for a renamed id (Alloy Map was `cytramap`): the new entry carries `replaces`, the old id keeps an unlisted copy pointing at the same jar with `renamedTo`. Later releases keep both in sync.
- Hub must not download from anywhere except this repo; do not host jars elsewhere.
- Mod repos that stay private and out of this repo: Alloy Boat (never released). Check the jar you are about to publish for anything that should not be public before running `release.py`.

## Release
- This repo is the release step for every mod. A mod jar is published only on the user's explicit OK.

## Gaps and improvement ideas
- `release.py` does not inspect the jar contents; add a pre-publish check (list of forbidden paths, expected nested jars) so an unintended bundle cannot be published.
- No script to verify the live manifest against the GitHub release assets (SHA-256 match for every entry); a `verify.py` would replace the manual checks in PROGRESS lines.
- No PROGRESS.txt or changelog for the repo itself; releases are recorded in each mod repo and git history.
- GitHub releases keep every old jar; no documented pruning rule except "count 1.20.4 releases separately".
