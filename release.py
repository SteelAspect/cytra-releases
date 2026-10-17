#!/usr/bin/env python3
"""Publish a Cytra mod jar to SteelAspect/cytra-releases and add it to manifest.json.

Usage: python release.py [--unlisted] <path-to-jar> "<changelog>"

--unlisted marks the mod "listed": false: Cytra Hub then only offers it as an update to players who already have it,
never as an install, and the download page leaves it out. The flag is kept on later releases of that mod.

Reads id, name, version, environment and required mods from fabric.mod.json inside the jar, creates the GitHub release
<id>-v<version> with the jar attached, updates manifest.json, then commits and pushes.
Refuses to run if that version is already in the manifest.

Then adds the release to Cytra Hub's built-in changelog (src/client/resources/cytra-hub/mods.json in the cytra-hub
checkout next to this repo, or $CYTRA_HUB) and commits it there on the current branch, without pushing. One changelog
line becomes one item; a leading "- " is dropped. Skipped for Cytra Hub itself, or when there's no checkout.
"""
import hashlib
import json
import os
import subprocess
import sys
import zipfile
from datetime import date

REPO = "SteelAspect/cytra-releases"
HERE = os.path.dirname(os.path.abspath(__file__))
MANIFEST = os.path.join(HERE, "manifest.json")
HUB = os.environ.get("CYTRA_HUB") or os.path.join(os.path.dirname(HERE), "cytra-hub")
HUB_MODS_JSON = os.path.join("src", "client", "resources", "cytra-hub", "mods.json")


def fail(msg):
    print("release.py: " + msg, file=sys.stderr)
    sys.exit(1)


def run(*cmd):
    print("$ " + " ".join(cmd))
    result = subprocess.run(cmd, cwd=HERE)
    if result.returncode != 0:
        fail("command failed: " + " ".join(cmd))


def read_mod_json(jar):
    try:
        with zipfile.ZipFile(jar) as z:
            # strict=False: some mods' descriptions contain raw control characters
            data = json.loads(z.read("fabric.mod.json").decode("utf-8"), strict=False)
    except KeyError:
        fail(jar + " has no fabric.mod.json")
    except zipfile.BadZipFile:
        fail(jar + " is not a jar")
    for key in ("id", "version"):
        if not isinstance(data.get(key), str) or not data[key]:
            fail("fabric.mod.json has no " + key)
    return data["id"], data.get("name") or data["id"], data["version"], extra_info(data), data.get("description") or ""


SKIP_DEPS = {"minecraft", "java", "fabricloader"}


def extra_info(data):
    """environment ("*", "client" or "server"), required mods and optional (recommends/suggests) mods, id -> version range."""
    def ranges(section):
        out = {}
        for dep, rng in (section or {}).items():
            if dep not in SKIP_DEPS:
                out[dep] = " || ".join(rng) if isinstance(rng, list) else str(rng)
        return out

    optional = ranges(data.get("suggests"))
    optional.update(ranges(data.get("recommends")))
    depends = ranges(data.get("depends"))
    return {"environment": data.get("environment") or "*", "depends": depends,
            "optional": {k: v for k, v in optional.items() if k not in depends}}


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def hub_change(version, items):
    lines = ",\n".join("        " + json.dumps(i, ensure_ascii=False) for i in items)
    return f'      {{"version": "{version}", "date": "{date.today().isoformat()}", "items": [\n{lines}\n      ]}},\n'


def update_hub(mod_id, name, description, version, changelog):
    """Add this release to Cytra Hub's mods.json, keeping its hand-written layout. Never fails the release."""
    path = os.path.join(HUB, HUB_MODS_JSON)
    if mod_id == "cytra-hub" or not os.path.isfile(path):
        return
    items = [line.strip().removeprefix("- ").strip() for line in changelog.splitlines()]
    items = [i for i in items if i]
    with open(path, encoding="utf-8") as f:
        text = f.read()
    try:
        data = json.loads(text)
    except ValueError as e:
        print(f"Cytra Hub: mods.json is not valid JSON ({e}), not updated")
        return
    if mod_id in data:
        if any(c.get("version") == version for c in data[mod_id].get("changelog", [])):
            return
        start = text.index(f'"{mod_id}": {{')
        marker = '"changelog": ['
        at = text.find(marker, start)
        if at < 0:
            print(f"Cytra Hub: {mod_id} has no changelog list in mods.json, not updated")
            return
        at = text.index("\n", at) + 1
        text = text[:at] + hub_change(version, items) + text[at:]
    else:
        end = text.rstrip().rindex("}")
        change = hub_change(version, items).rstrip().rstrip(",")
        text = (text[:end].rstrip() + f',\n  "{mod_id}": {{\n    "name": {json.dumps(name, ensure_ascii=False)},\n'
                f'    "description": {json.dumps(description, ensure_ascii=False)},\n    "changelog": [\n{change}\n    ]\n  }}\n}}\n')
    json.loads(text)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    for cmd in (["git", "add", HUB_MODS_JSON], ["git", "commit", "-q", "-m", f"Changelog: {name} {version}"]):
        if subprocess.run(cmd, cwd=HUB).returncode != 0:
            print("Cytra Hub: could not commit mods.json, the change is left in the working tree")
            return
    print(f"Cytra Hub: added {name} {version} to mods.json and committed it in {HUB} (not pushed). "
          f"It reaches players with the next Cytra Hub release.")
    if mod_id not in data:
        print(f"Cytra Hub: {mod_id} is new; add a put(...) line in ModCatalog.java so the Hub shows its page.")


def main():
    args = sys.argv[1:]
    unlisted = "--unlisted" in args
    args = [a for a in args if a != "--unlisted"]
    if len(args) != 2:
        fail('usage: python release.py [--unlisted] <path-to-jar> "<changelog>"')
    jar, changelog = os.path.abspath(args[0]), args[1].strip()
    if not os.path.isfile(jar):
        fail("no such file: " + jar)
    if not changelog:
        fail("changelog is empty")

    mod_id, name, version, extra, description = read_mod_json(jar)
    jar_name = os.path.basename(jar)
    tag = f"{mod_id}-v{version}"

    run("git", "pull", "--ff-only", "-q")
    with open(MANIFEST, encoding="utf-8") as f:
        manifest = json.load(f)
    mods = manifest.setdefault("mods", [])
    entry = next((m for m in mods if m.get("id") == mod_id), None)
    if entry is not None and entry.get("version") == version:
        fail(f"{name} {version} is already in the manifest")

    digest = sha256(jar)
    print(f"{name} ({mod_id}) {version}\nsha256 {digest}")
    run("gh", "release", "create", tag, jar, "-R", REPO, "--title", f"{name} {version}", "--notes", changelog)

    new_entry = {
        "id": mod_id,
        "name": name,
        "version": version,
        "url": f"https://github.com/{REPO}/releases/download/{tag}/{jar_name}",
        "sha256": digest,
        "changelog": changelog,
        **extra,
    }
    if unlisted or (entry is not None and entry.get("listed") is False):
        new_entry["listed"] = False
    if entry is None:
        mods.append(new_entry)
    else:
        mods[mods.index(entry)] = new_entry
    mods.sort(key=lambda m: m.get("name", "").lower())
    with open(MANIFEST, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
        f.write("\n")

    run("git", "add", "manifest.json")
    run("git", "commit", "-q", "-m", f"{name} {version}")
    run("git", "push", "-q")
    print(f"Released {name} {version}: https://github.com/{REPO}/releases/tag/{tag}")
    update_hub(mod_id, name, description, version, changelog)


if __name__ == "__main__":
    main()
