# Alloy Releases

Public jars for the Alloy Fabric mods (Minecraft 1.21.11), plus:

- **Download page:** https://steelaspect.github.io/cytra-releases/
- **Update manifest:** https://steelaspect.github.io/cytra-releases/manifest.json, which Alloy Hub's Updates tab reads.

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
6. Adds the release to Alloy Hub's built-in changelog (`src/client/resources/cytra-hub/mods.json` in the `cytra-hub`
   checkout next to this repo, or the folder in `$CYTRA_HUB`) and commits it there, without pushing. Each line of the
   changelog becomes one item (a leading `- ` is dropped). Players see it with the next Alloy Hub release. Skipped for
   Alloy Hub itself and when there is no checkout. A brand-new mod also needs a `put(...)` line in Hub's
   `ModCatalog.java`; the script reminds you.

It refuses to run if that version of the mod is already in the manifest. Bump the version in the mod first.

Add `--unlisted` (e.g. `python release.py --unlisted <jar> "<changelog>"`) for a mod that should only be updated,
never offered: it gets `"listed": false`, so Alloy Hub shows it only to players who already have it (as an update) and
the download page leaves it out. Later releases of that mod keep the flag. Alloy Mass Craft is released this way.

Add `--replaces <old-id>` when a mod's id changed (Alloy Map was `cytramap`): the entry gets `"replaces": ["cytramap"]`,
and `cytramap` gets an unlisted copy of the entry (same jar, `"renamedTo": "alloymap"`). Any Hub then updates the old
mod to the renamed jar, and Alloy Hub 0.5.1+ doesn't offer the renamed mod as a second install while the old one is
there. Later releases keep both in sync without the flag.

## Manifest format

```json
{
  "mods": [
    {
      "id": "cytra-hub",
      "name": "Alloy Hub",
      "version": "0.2.0",
      "url": "https://github.com/SteelAspect/cytra-releases/releases/download/cytra-hub-v0.2.0/cytra-hub-0.2.0.jar",
      "sha256": "…",
      "changelog": "…",
      "environment": "*",
      "depends": {"fabric-api": "*"},
      "optional": {"modmenu": "*"},
      "listed": true
    }
  ]
}
```

`environment` (`*`, `client` or `server`), `depends` (required mods) and `optional` (recommended or suggested mods) come from the jar's fabric.mod.json. Alloy Hub lists them next to the Install button for mods you don't have.

Alloy Hub only updates mods whose `id` is in the manifest and whose `url` starts with `https://github.com/SteelAspect/cytra-releases/`. It checks the SHA-256 before installing anything.

## If something goes wrong

- **The release was created but the push failed:** fix the problem, then run `git push`.
- **The release was created but `manifest.json` was not updated:** delete the release and its tag, then run `release.py` again:

  ```
  gh release delete <tag> -R SteelAspect/cytra-releases --cleanup-tag
  ```
