#!/usr/bin/env python3
"""Publish a Cytra mod jar to SteelAspect/cytra-releases and add it to manifest.json.

Usage: python release.py <path-to-jar> "<changelog>"

Reads id, name, version, environment and required mods from fabric.mod.json inside the jar, creates the GitHub release
<id>-v<version> with the jar attached, updates manifest.json, then commits and pushes.
Refuses to run if that version is already in the manifest.
"""
import hashlib
import json
import os
import subprocess
import sys
import zipfile

REPO = "SteelAspect/cytra-releases"
HERE = os.path.dirname(os.path.abspath(__file__))
MANIFEST = os.path.join(HERE, "manifest.json")


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
    return data["id"], data.get("name") or data["id"], data["version"], extra_info(data)


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


def main():
    if len(sys.argv) != 3:
        fail('usage: python release.py <path-to-jar> "<changelog>"')
    jar, changelog = os.path.abspath(sys.argv[1]), sys.argv[2].strip()
    if not os.path.isfile(jar):
        fail("no such file: " + jar)
    if not changelog:
        fail("changelog is empty")

    mod_id, name, version, extra = read_mod_json(jar)
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


if __name__ == "__main__":
    main()
