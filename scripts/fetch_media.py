#!/usr/bin/env python
"""Localise Squarespace CDN images referenced by the content JSON.

Downloads every remote image, converts it to WebP, stores it under
public/images/<collection>/<slug>-NN.webp, rewrites the content JSON to point
at the local path, and writes content/media-map.json so every substitution is
traceable.

Run:
    python scripts/fetch_media.py --dry-run     # report only
    python scripts/fetch_media.py               # download + rewrite

The original remote URL is preserved in media-map.json, so the step is
reversible: pass --revert to put the remote URLs back.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import unquote, urlparse

import requests
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
CONTENT = ROOT / "content"
IMAGES = ROOT / "public" / "images"
MAP_FILE = CONTENT / "media-map.json"

# Squarespace serves images from these hosts.
REMOTE_HOSTS = ("squarespace-cdn.com", "squarespace.com")

IMG_RE = re.compile(
    r"https?://[^\"\\\s)]+?\.(?:jpg|jpeg|png|webp|gif)(?:\?[^\"\\\s)]*)?", re.I
)

# A realistic browser UA; Squarespace's CDN rejects the default requests one.
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/122.0 Safari/537.36"
    ),
    "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
}

MAX_WEBP_WIDTH = 1800  # plenty for the layouts used; keeps files small
WEBP_QUALITY = 82

# Proxy: the sandbox routes through the local Clash instance. Honour the
# environment if present, else try the known-good port.
PROXIES = {"http": "http://127.0.0.1:33352", "https": "http://127.0.0.1:33352"}


def is_remote(url: str) -> bool:
    return any(h in url for h in REMOTE_HOSTS)


def slugify(text: str, fallback: str = "image") -> str:
    """ASCII-safe slug; CJK is dropped rather than transliterated."""
    text = unquote(text)
    text = re.sub(r"\.(jpg|jpeg|png|webp|gif)$", "", text, flags=re.I)
    text = re.sub(r"^\d{13}[-_]?", "", text)          # leading epoch stamp
    text = re.sub(r"[^A-Za-z0-9]+", "-", text).strip("-").lower()
    text = re.sub(r"-{2,}", "-", text)
    return text[:48] or fallback


def collect() -> dict[Path, list[str]]:
    """Map each content file to the remote URLs it references."""
    out: dict[Path, list[str]] = {}
    for path in sorted(CONTENT.rglob("*.json")):
        if path.name == "media-map.json":
            continue
        text = path.read_text(encoding="utf-8")
        urls = sorted({u for u in IMG_RE.findall(text) if is_remote(u)})
        if urls:
            out[path] = urls
    return out


def plan_names(files: dict[Path, list[str]]) -> dict[str, str]:
    """Build remote-URL -> local-path mapping, grouped by collection."""
    # Reuse one download for URLs referenced from several files.
    grouped: dict[str, list[tuple[Path, int]]] = {}
    for path, urls in files.items():
        for idx, url in enumerate(urls, 1):
            grouped.setdefault(url, []).append((path, idx))

    mapping: dict[str, str] = {}
    used: set[str] = set()
    for url, refs in grouped.items():
        path, idx = refs[0]
        rel = path.relative_to(CONTENT)
        parts = rel.parts
        # content/items/<collection>--<slug>.json  ->  <collection>
        # content/pages/<name>.json                ->  pages
        if parts[0] == "items" and len(parts) > 1 and "--" in parts[1]:
            collection = parts[1].split("--", 1)[0]
        else:
            collection = "pages"
        stem = slugify(path.stem)
        # Drop the collection prefix from the filename where it repeats it.
        if "--" in stem:
            stem = stem.split("--", 1)[1]
        if stem.startswith(collection + "-"):
            stem = stem[len(collection) + 1:]
        if collection == "pages" and stem.startswith("pages-"):
            stem = stem[6:]
        stem = stem[:40]

        base = f"{collection}/{stem}-{idx:02d}"
        candidate = base
        n = 1
        while candidate in used:
            n += 1
            candidate = f"{base}-{n}"
        used.add(candidate)
        mapping[url] = f"/images/{candidate}.webp"
    return mapping


def download(url: str, tries: int = 3) -> bytes | None:
    for attempt in range(1, tries + 1):
        try:
            r = requests.get(url, headers=HEADERS, timeout=45, proxies=PROXIES)
            if r.status_code == 200 and len(r.content) > 512:
                return r.content
            print(f"    HTTP {r.status_code}, {len(r.content)}B (try {attempt})")
        except Exception as exc:  # noqa: BLE001
            print(f"    {type(exc).__name__}: {str(exc)[:70]} (try {attempt})")
        time.sleep(1.5 * attempt)
    return None


def to_webp(raw: bytes) -> tuple[bytes, tuple[int, int]] | None:
    try:
        im = Image.open(io.BytesIO(raw))
        im.load()
    except Exception as exc:  # noqa: BLE001
        print(f"    decode failed: {exc}")
        return None

    if im.mode in ("RGBA", "LA", "P"):
        im = im.convert("RGBA")
    else:
        im = im.convert("RGB")

    if im.width > MAX_WEBP_WIDTH:
        ratio = MAX_WEBP_WIDTH / im.width
        im = im.resize(
            (MAX_WEBP_WIDTH, max(1, round(im.height * ratio))), Image.LANCZOS
        )

    buf = io.BytesIO()
    im.save(buf, "WEBP", quality=WEBP_QUALITY, method=5)
    return buf.getvalue(), im.size


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="report only")
    ap.add_argument("--revert", action="store_true", help="restore remote URLs")
    args = ap.parse_args()

    if args.revert:
        return revert()

    files = collect()
    if not files:
        print("No remote images found — nothing to do.")
        return 0

    mapping = plan_names(files)
    print(f"content files with remote images : {len(files)}")
    print(f"unique remote images             : {len(mapping)}")
    print()

    if args.dry_run:
        for url, local in list(mapping.items())[:12]:
            print(f"  {local}")
            print(f"    <- {url[:104]}")
        print(f"  ... and {max(0, len(mapping) - 12)} more")
        return 0

    IMAGES.mkdir(parents=True, exist_ok=True)
    for url, local in mapping.items():
        (IMAGES.parent / local.lstrip("/")).parent.mkdir(parents=True, exist_ok=True)

    ok: dict[str, str] = {}
    failed: list[str] = []
    stats: list[tuple[str, int, int]] = []

    with ThreadPoolExecutor(max_workers=6) as pool:
        futures = {pool.submit(download, u): u for u in mapping}
        for fut in as_completed(futures):
            url = futures[fut]
            local = mapping[url]
            dest = IMAGES.parent / local.lstrip("/")
            raw = fut.result()
            if raw is None:
                print(f"  FAIL {url[:96]}")
                failed.append(url)
                continue
            conv = to_webp(raw)
            if conv is None:
                print(f"  CONV-FAIL {local}")
                failed.append(url)
                continue
            data, (w, h) = conv
            dest.write_bytes(data)
            ok[url] = local
            stats.append((local, len(raw), len(data)))
            print(f"  ok  {local:58} {len(raw)//1024:5}K -> {len(data)//1024:4}K")

    print()
    print(f"downloaded {len(ok)} / {len(mapping)}")
    if stats:
        before = sum(a for _, a, _ in stats)
        after = sum(b for _, _, b in stats)
        print(f"bytes: {before/1048576:.2f}MB -> {after/1048576:.2f}MB "
              f"({100 - after*100//before}% smaller)")

    if failed:
        print()
        print(f"{len(failed)} failed — content files left untouched for those URLs.")

    # Rewrite the JSON. Only substitute URLs that downloaded successfully.
    rewritten = 0
    for path in files:
        text = path.read_text(encoding="utf-8")
        new = text
        for url, local in ok.items():
            if url in new:
                new = new.replace(url, local)
        if new != text:
            path.write_text(new, encoding="utf-8")
            rewritten += 1

    MAP_FILE.write_text(
        json.dumps(
            {
                "generatedBy": "scripts/fetch_media.py",
                "note": "remote URL -> local path; run with --revert to undo",
                "images": {
                    u: {"local": l, "sha1": hashlib.sha1(u.encode()).hexdigest()[:12]}
                    for u, l in sorted(ok.items())
                },
                "failed": failed,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    print()
    print(f"rewrote {rewritten} content files")
    print(f"map written to {MAP_FILE.relative_to(ROOT)}")
    return 0 if not failed else 1


def revert() -> int:
    if not MAP_FILE.exists():
        print("No media-map.json — nothing to revert.")
        return 1
    data = json.loads(MAP_FILE.read_text(encoding="utf-8"))
    pairs = [(v["local"], u) for u, v in data.get("images", {}).items()]
    n = 0
    for path in sorted(CONTENT.rglob("*.json")):
        if path.name == "media-map.json":
            continue
        text = path.read_text(encoding="utf-8")
        new = text
        for local, remote in pairs:
            if local in new:
                new = new.replace(local, remote)
        if new != text:
            path.write_text(new, encoding="utf-8")
            n += 1
    print(f"reverted {n} files to remote URLs")
    return 0


if __name__ == "__main__":
    sys.exit(main())
