#!/usr/bin/env python3
"""Checks the index: every packages/NAME.toml has the fields it needs, in the form they take.

    python3 tools/check.py            # the files themselves
    python3 tools/check.py --remote   # also each repository: public, a vX.Y.Z tag, and an
                                      # eskiu.toml at that tag whose [package] name is NAME
    python3 tools/check.py --json     # the index as JSON on stdout (for the site and tools)

Python 3.11 or newer (tomllib). Exits with 1 and the problems when there are any.
"""

import json
import os
import re
import subprocess
import sys
import tempfile
import tomllib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PACKAGES = os.path.join(ROOT, "packages")

# eskiuc takes letters, digits and '_' in a package name; the index also wants it lower case,
# so two entries cannot differ only by case.
NAME = re.compile(r"^[a-z][a-z0-9_]*$")
GIT = re.compile(r"^https://[A-Za-z0-9.-]+/[A-Za-z0-9._/-]+$")
KEYWORD = re.compile(r"^[a-z0-9][a-z0-9-]*$")
TAG = re.compile(r"^v(\d+)\.(\d+)\.(\d+)$")
REQUIRED = {"name": str, "git": str, "description": str, "license": str}
OPTIONAL = {"keywords": list, "maintainers": list, "homepage": str}


def check_entry(path, problems):
    file = os.path.basename(path)
    try:
        with open(path, "rb") as f:
            entry = tomllib.load(f)
    except tomllib.TOMLDecodeError as e:
        problems.append(f"{file}: not TOML: {e}")
        return None
    for key, kind in REQUIRED.items():
        if not isinstance(entry.get(key), kind) or not entry.get(key):
            problems.append(f"{file}: '{key}' is missing or not a {kind.__name__}")
    for key in entry:
        if key not in REQUIRED and key not in OPTIONAL:
            problems.append(f"{file}: unknown key '{key}'")
        elif key in OPTIONAL and not isinstance(entry[key], OPTIONAL[key]):
            problems.append(f"{file}: '{key}' is not a {OPTIONAL[key].__name__}")
    name = entry.get("name", "")
    if isinstance(name, str):
        if not NAME.match(name):
            problems.append(f"{file}: name '{name}': lower-case letters, digits and '_', starting with a letter")
        if file != f"{name}.toml":
            problems.append(f"{file}: the file is named after the package: {name}.toml")
    if isinstance(entry.get("git"), str) and not GIT.match(entry["git"]):
        problems.append(f"{file}: git '{entry['git']}': an https URL of a public repository")
    if isinstance(entry.get("description"), str) and len(entry["description"]) > 160:
        problems.append(f"{file}: description is over 160 characters")
    for k in entry.get("keywords", []) if isinstance(entry.get("keywords"), list) else []:
        if not isinstance(k, str) or not KEYWORD.match(k):
            problems.append(f"{file}: keyword '{k}': lower case, digits and '-'")
    if isinstance(entry.get("keywords"), list) and len(entry["keywords"]) > 8:
        problems.append(f"{file}: at most 8 keywords")
    return entry


def latest_tag(url):
    out = subprocess.run(["git", "ls-remote", "--tags", "--refs", url], capture_output=True, text=True,
                         env={**os.environ, "GIT_TERMINAL_PROMPT": "0"}, timeout=120)
    if out.returncode != 0:
        return None, "the repository cannot be read (is it public?)"
    tags = []
    for line in out.stdout.splitlines():
        ref = line.split("\t")[-1].removeprefix("refs/tags/")
        m = TAG.match(ref)
        if m:
            tags.append((tuple(int(x) for x in m.groups()), ref))
    if not tags:
        return None, "no release tag (vX.Y.Z)"
    return max(tags)[1], None


def check_remote(entry, problems):
    file = f"{entry['name']}.toml"
    tag, err = latest_tag(entry["git"])
    if err:
        problems.append(f"{file}: {entry['git']}: {err}")
        return
    with tempfile.TemporaryDirectory() as tmp:
        out = subprocess.run(["git", "clone", "--quiet", "--depth", "1", "--branch", tag, entry["git"], tmp],
                             capture_output=True, text=True, env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
                             timeout=300)
        if out.returncode != 0:
            problems.append(f"{file}: {tag} cannot be checked out")
            return
        manifest = os.path.join(tmp, "eskiu.toml")
        if not os.path.exists(manifest):
            problems.append(f"{file}: no eskiu.toml at {tag}")
            return
        with open(manifest, "rb") as f:
            try:
                pkg = tomllib.load(f).get("package", {})
            except tomllib.TOMLDecodeError as e:
                problems.append(f"{file}: eskiu.toml at {tag} is not TOML: {e}")
                return
        if pkg.get("name") != entry["name"]:
            problems.append(f"{file}: eskiu.toml at {tag} names the package '{pkg.get('name')}', not '{entry['name']}'")
    entry["latest"] = tag


def main():
    remote = "--remote" in sys.argv
    as_json = "--json" in sys.argv
    problems = []
    entries = []
    for file in sorted(os.listdir(PACKAGES)):
        if not file.endswith(".toml"):
            problems.append(f"{file}: only NAME.toml files go in packages/")
            continue
        entry = check_entry(os.path.join(PACKAGES, file), problems)
        if entry:
            entries.append(entry)
    gits = {}
    for e in entries:
        g = e.get("git", "").rstrip("/").removesuffix(".git").lower()
        if g in gits:
            problems.append(f"{e.get('name')}.toml: the same repository as {gits[g]}.toml")
        gits[g] = e.get("name")
    if remote and not problems:
        for e in entries:
            check_remote(e, problems)
    if problems:
        print("\n".join(problems), file=sys.stderr)
        sys.exit(1)
    if as_json:
        json.dump({"packages": entries}, sys.stdout, indent=2, ensure_ascii=False)
        print()
    else:
        print(f"{len(entries)} packages ok" + (" (repositories checked)" if remote else ""))


if __name__ == "__main__":
    main()
