#!/usr/bin/env python
"""Drop image files that the built site never references.

`fetch_media.py` downloads every remote image a content file mentions. Some of
those turn out to be redundant once the templates are taken into account — most
commonly `meta.ogImage` thumbnails, which are only a fallback for articles that
have no real images of their own.

This script:
  1. walks dist/ and collects every /images/*.webp actually referenced;
  2. lists files present in public/images but never referenced;
  3. with --apply, deletes them and strips the matching reference from content
     JSON so the content stays self-consistent.

Safe by default (dry run). Deletions go to a timestamped backup folder rather
than being unlinked outright.

Run:
    python scripts/prune_media.py
    python scripts/prune_media.py --apply
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PUBLIC_IMAGES = ROOT / "public" / "images"
DIST = ROOT / "dist"
CONTENT = ROOT / "content"
MAP_FILE = CONTENT / "media-map.json"

IMG_REF = re.compile(r"/images/([A-Za-z0-9._/-]+\.webp)")


def referenced_in_dist() -> set[str]:
    used: set[str] = set()
    for path in DIST.rglob("*.html"):
        text = path.read_text(encoding="utf-8", errors="ignore")
        used.update(IMG_REF.findall(text))
    return used


def on_disk() -> set[str]:
    return {
        p.relative_to(PUBLIC_IMAGES).as_posix()
        for p in PUBLIC_IMAGES.rglob("*.webp")
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="actually prune")
    args = ap.parse_args()

    if not DIST.exists():
        print("dist/ not found — run `npm run build` first.")
        return 1

    used = referenced_in_dist()
    disk = on_disk()
    unused = sorted(disk - used)

    print(f"on disk    : {len(disk)}")
    print(f"referenced : {len(used)}")
    print(f"unused     : {len(unused)}")
    print()

    if not unused:
        print("Nothing to prune.")
        return 0

    total = sum((PUBLIC_IMAGES / u).stat().st_size for u in unused)

    # Which content files mention each unused path?
    refs: dict[str, list[Path]] = {}
    for u in unused:
        needle = "/images/" + u
        for path in CONTENT.rglob("*.json"):
            if path.name == "media-map.json":
                continue
            if needle in path.read_text(encoding="utf-8"):
                refs.setdefault(u, []).append(path)

    for u in unused:
        size = (PUBLIC_IMAGES / u).stat().st_size // 1024
        where = ", ".join(p.name for p in refs.get(u, [])) or "(no code reference)"
        print(f"  {u:58} {size:4}K  {where}")

    print()
    print(f"total reclaimable: {total // 1024} KB")

    if not args.apply:
        print()
        print("dry run — re-run with --apply to remove.")
        return 0

    backup = ROOT / f".media-backup-{time.strftime('%Y%m%d-%H%M%S')}"
    backup.mkdir(parents=True, exist_ok=True)

    for u in unused:
        dest = backup / u
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(PUBLIC_IMAGES / u), str(dest))

    # Strip the dangling references from content JSON.
    changed = 0
    for path in sorted(set(p for ps in refs.values() for p in ps)):
        text = path.read_text(encoding="utf-8")
        new = text
        for u in unused:
            needle = "/images/" + u
            if needle in new:
                new = new.replace(needle, "")
        if new != text:
            path.write_text(new, encoding="utf-8")
            changed += 1

    # Drop pruned entries from the media map so it stays truthful.
    if MAP_FILE.exists():
        data = json.loads(MAP_FILE.read_text(encoding="utf-8"))
        keep = {
            url: meta
            for url, meta in data.get("images", {}).items()
            if meta["local"].lstrip("/").replace("images/", "", 1) not in unused
        }
        data["images"] = keep
        data["prunedAt"] = time.strftime("%Y-%m-%d %H:%M:%S")
        MAP_FILE.write_text(
            json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    print()
    print(f"moved {len(unused)} files to {backup.name}/")
    print(f"cleaned {changed} content files")
    print("Re-run `npm run build` to confirm.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
