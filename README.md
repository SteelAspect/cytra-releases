# Cytra Releases

Public jars for the Cytra Fabric mods (Minecraft 1.21.11), plus:

- **Download page:** https://steelaspect.github.io/cytra-releases/
- **Update manifest:** https://steelaspect.github.io/cytra-releases/manifest.json, which Cytra Hub's Updates tab reads.

## Releasing a mod

You need Python 3, the `gh` CLI (logged in with push access to this repo) and a clone of this repo.

```
python release.py <path-to-jar> "<changelog>"
```

Example:

```
python release.py ~/Documents/Mods/cytra-hub/build/libs/cytra-hub-0.2.0.jar "New Updates tab"
```

What it does:

1. Reads `id`, `name` and `version` from `fabric.mod.json` inside the jar.
2. Works out the jar's SHA-256.
3. Creates the GitHub release `<id>-v<version>` here, with the jar attached.
4. Adds or replaces that mod's entry in `manifest.json`.
5. Commits and pushes. The page and manifest update within a few minutes.

It refuses to run if that version of the mod is already in the manifest. Bump the version in the mod first.

## Manifest format

```json
{
  "mods": [
    {
      "id": "cytra-hub",
      "name": "Cytra Hub",
      "version": "0.2.0",
      "url": "https://github.com/SteelAspect/cytra-releases/releases/download/cytra-hub-v0.2.0/cytra-hub-0.2.0.jar",
      "sha256": "…",
      "changelog": "…"
    }
  ]
}
```

Cytra Hub only updates mods whose `id` is in the manifest and whose `url` starts with `https://github.com/SteelAspect/cytra-releases/`. It checks the SHA-256 before installing anything.

## If something goes wrong

- **The release was created but the push failed:** fix the problem, then run `git push`.
- **The release was created but `manifest.json` was not updated:** delete the release and its tag, then run `release.py` again:

  ```
  gh release delete <tag> -R SteelAspect/cytra-releases --cleanup-tag
  ```
