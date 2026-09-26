"""
Parallel crawler for atlasofshenzhen.cn.

Reads a list of site-relative paths and mirrors each page to disk.
Uses a thread pool and validates every response (status + size) so a
silent 404 or a truncated body can never pollute the content set.

Run:  python scripts/crawl.py <links_file> <out_dir>
"""

from __future__ import annotations

import concurrent.futures as cf
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

BASE = "https://www.atlasofshenzhen.cn"
UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
)
MIN_BYTES = 20_000          # anything smaller is an error page
WORKERS = 6
RETRIES = 3


def slugify(path: str) -> str:
    return path.strip("/").replace("/", "__") + ".html"


def fetch(path: str) -> tuple[str, str, int]:
    url = BASE + path
    last_err = ""
    for attempt in range(RETRIES):
        try:
            req = urllib.request.Request(
                url, headers={"User-Agent": UA, "Accept-Language": "en"}
            )
            with urllib.request.urlopen(req, timeout=45) as r:
                body = r.read()
                return path, body.decode("utf-8", errors="ignore"), len(body)
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            last_err = str(e)
            time.sleep(1.5 * (attempt + 1))
    return path, "", -len(last_err)


def main() -> int:
    links_file = Path(sys.argv[1])
    out = Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)

    paths = [
        ln.strip() for ln in links_file.read_text(encoding="utf-8").splitlines()
        if ln.strip()
    ]
    print(f"Crawling {len(paths)} pages with {WORKERS} workers...\n")

    ok = 0
    bad: list[str] = []

    with cf.ThreadPoolExecutor(max_workers=WORKERS) as pool:
        for path, body, size in pool.map(fetch, paths):
            if size >= MIN_BYTES:
                (out / slugify(path)).write_text(body, encoding="utf-8")
                ok += 1
                print(f"  OK   {size:>8,}  {path}")
            else:
                bad.append(f"{path}  (size={size})")
                print(f"  FAIL {size:>8,}  {path}")

    print(f"\n{ok}/{len(paths)} succeeded -> {out}")
    if bad:
        print("\nFailed pages:")
        for b in bad:
            print("  -", b)
    return 0 if not bad else 1


if __name__ == "__main__":
    raise SystemExit(main())
