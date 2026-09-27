#!/usr/bin/env python
"""Point video ogImage metadata at YouTube instead of the Squarespace CDN.

Video items carry a dead-ish `meta.ogImage` on static1.squarespace.com (a
URL with no file extension, e.g. `.../t/<id>/<epoch>/?format=1500w`). Those
break the moment the Squarespace subscription lapses.

Because each video already has a `youtubeId`, the natural replacement is
YouTube's own poster frame:
    https://i.ytimg.com/vi/<id>/maxresdefault.jpg     (preferred)
    https://i.ytimg.com/vi/<id>/hqdefault.jpg         (guaranteed fallback)

`maxresdefault` does not exist for every upload, so this script HEAD-checks
each candidate and falls back to `hqdefault` when maxres is missing.

Run:
    python scripts/fix_video_og.py --dry-run
    python scripts/fix_video_og.py
"""

from __future__ import annotations

import argparse
import glob
import json
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
ITEMS = ROOT / "content" / "items"

PROXIES = {"http": "http://127.0.0.1:33352", "https": "http://127.0.0.1:33352"}
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}


def yt_thumb(vid: str) -> str:
    for name in ("maxresdefault", "hqdefault"):
        url = f"https://i.ytimg.com/vi/{vid}/{name}.jpg"
        try:
            r = requests.head(
                url, headers=HEADERS, timeout=20, proxies=PROXIES, allow_redirects=True
            )
            if r.status_code == 200:
                return url
        except Exception:  # noqa: BLE001
            continue
    return f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    targets = []
    for f in sorted(glob.glob(str(ITEMS / "videos--*.json"))):
        d = json.loads(Path(f).read_text(encoding="utf-8"))
        og = (d.get("meta") or {}).get("ogImage") or ""
        vid = d.get("youtubeId")
        if "squarespace" in og and vid:
            targets.append((Path(f), vid, og))

    print(f"video items needing ogImage fix: {len(targets)}")
    if not targets:
        return 0

    if args.dry_run:
        for f, vid, og in targets[:6]:
            print(f"  {f.name[:52]}")
            print(f"    {og[:88]}")
            print(f"    -> https://i.ytimg.com/vi/{vid}/maxresdefault.jpg")
        print(f"  ... and {max(0, len(targets) - 6)} more")
        return 0

    resolved: dict[str, str] = {}
    with ThreadPoolExecutor(max_workers=8) as pool:
        futs = {pool.submit(yt_thumb, vid): vid for _, vid, _ in targets}
        for fut in as_completed(futs):
            vid = futs[fut]
            try:
                resolved[vid] = fut.result()
            except Exception:  # noqa: BLE001
                resolved[vid] = f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg"

    changed = 0
    for f, vid, og in targets:
        d = json.loads(f.read_text(encoding="utf-8"))
        new = resolved[vid]
        if d["meta"].get("ogImage") != new:
            d["meta"]["ogImage"] = new
            f.write_text(
                json.dumps(d, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
            )
            changed += 1

    maxres = sum(1 for u in resolved.values() if "maxresdefault" in u)
    print(f"rewrote {changed} video items")
    print(f"  maxresdefault: {maxres}")
    print(f"  hqdefault    : {len(resolved) - maxres}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
