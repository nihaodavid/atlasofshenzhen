"""
Extract structured content from crawled atlasofshenzhen.cn pages.

The original Squarespace 7.1 site uses three distinct content shapes:

  1. FLUID-ENGINE  (home, aboutthis, team, faq, join-us, future-works-1)
     Content sits in <div class="sqs-html-content"> blocks.

  2. LESSONS LIST  (videos)
     Content sits in <li class="grid-item"> cards -> each links to a detail
     page carrying the YouTube embed.

  3. BLOG COLLECTION (history, books, nature, service, manufacturers-1)
     Content sits in <article class="blog-item"> cards -> each links to a
     detail page carrying the article body.

Detail pages add:
  - video  : data-config-embed-video JSON (YouTube id + title)
  - article: <div class="blog-item-wrapper"> ... rich text body

Output (uniform JSON, one file per page + one per detail item):
  content/pages/<slug>.json
  content/items/<slug>.json
  content/manifest.json

Run:  python scripts/extract.py <crawled_dir> <out_dir>
"""

from __future__ import annotations

import html
import json
import re
import sys
from pathlib import Path

# crawled file -> (slug, nav title, url path, kind)
PAGES: list[tuple[str, str, str, str, str]] = [
    ("home.html",            "index",           "Home",             "",                "fluid"),
    ("videos.html",          "videos",          "Videos",           "videos",          "lessons"),
    ("aboutthis.html",       "aboutthis",       "Vision & Mission", "aboutthis",       "fluid"),
    ("team.html",            "team",            "Team",             "team",            "fluid"),
    ("faq.html",             "faq",             "FAQ",              "faq",             "fluid"),
    ("join-us.html",         "join-us",         "Join Us",          "join-us",         "fluid"),
    ("future-works-1.html",  "future-works-1",  "Future Works",     "future-works-1",  "fluid"),
    ("history.html",         "history",         "History",          "history",         "blog"),
    ("books.html",           "books",           "Books",            "books",           "blog"),
    ("manufacturers-1.html", "manufacturers-1", "Manufacturers",    "manufacturers-1", "blog"),
    ("service.html",         "service",         "Service",          "service",         "blog"),
    ("nature.html",          "nature",          "Nature",           "nature",          "blog"),
]

# ------------------------------------------------------------------- regexes
# Nested <li>/<article> break non-greedy matching, so we split on opening tags.
RE_SPLIT_GRID = re.compile(r'(?=<li\s+class="\s*\n?\s*grid-item)')
RE_SPLIT_BLOG = re.compile(r'(?=<article\s+[^>]*class="[^"]*blog-item)')
RE_SQS_HTML = re.compile(
    r'<div class="sqs-html-content"[^>]*>(.*?)(?:</div>\s*<style|</div>\s*</div>)', re.S
)

RE_HEADING = re.compile(r"<h([1-6])[^>]*>(.*?)</h\1>", re.S | re.I)
RE_PARA = re.compile(r"<p[^>]*>(.*?)</p>", re.S | re.I)
RE_LI = re.compile(r"<li[^>]*>(.*?)</li>", re.S | re.I)
RE_YT_THUMB = re.compile(r"i\.ytimg\.com/vi/([A-Za-z0-9_\-]{11})")
RE_YT_EMBED = re.compile(r"youtube(?:-nocookie)?\.com/embed/([A-Za-z0-9_\-]{11})")
RE_IMG_SRC = re.compile(r'<img[^>]*\ssrc="([^"]+)"', re.I)
RE_IMG_ALT = re.compile(r'<img[^>]*\salt="([^"]*)"', re.I)
RE_SRCSET = re.compile(r'srcset="([^"\s]+)')
RE_SQS_IMG = re.compile(r"https://images\.squarespace-cdn\.com/content/[^\"'\s)\\]+")


# --------------------------------------------------------------- text helpers
def text_of(raw: str) -> str:
    """Flatten HTML to readable text without losing block boundaries."""
    raw = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", raw, flags=re.S | re.I)
    raw = re.sub(r"<br\s*/?>", "\n", raw, flags=re.I)
    raw = re.sub(r"</(p|div|h[1-6]|li|blockquote)>", "\n", raw, flags=re.I)
    raw = re.sub(r"<li[^>]*>", "- ", raw, flags=re.I)
    raw = re.sub(r"<[^>]+>", " ", raw)
    raw = html.unescape(raw).replace("\xa0", " ")
    raw = re.sub(r"[ \t]+", " ", raw)
    raw = re.sub(r"\n\s*\n+", "\n\n", raw)
    return raw.strip()


def best_image(tag: str) -> str | None:
    """Prefer the largest srcset candidate; normalise to ?format=original."""
    m = RE_SRCSET.search(tag) or RE_IMG_SRC.search(tag)
    if not m:
        return None
    url = m.group(1)
    if not url.startswith("http"):
        return None
    if "squarespace-cdn.com" in url:
        url = re.sub(r"\?format=\d+w.*$", "?format=original", url)
    return url


def dedupe(blocks: list[dict]) -> list[dict]:
    """Squarespace repeats labels for desktop + mobile nav; drop exact repeats."""
    seen: set[str] = set()
    out: list[dict] = []
    for b in blocks:
        t = b.get("text", "")
        if not t or t in seen:
            continue
        seen.add(t)
        out.append(b)
    return out


# ----------------------------------------------------- shape 1: fluid engine
def extract_fluid(doc: str) -> list[dict]:
    blocks: list[dict] = []
    for m in RE_SQS_HTML.finditer(doc):
        inner = m.group(1)
        # preserve document order across headings / paragraphs / list items
        positioned: list[tuple[int, dict]] = []
        for hm in RE_HEADING.finditer(inner):
            t = text_of(hm.group(2))
            if t:
                positioned.append(
                    (hm.start(), {"type": "heading",
                                  "level": int(hm.group(1)), "text": t})
                )
        for pm in RE_PARA.finditer(inner):
            if RE_HEADING.search(pm.group(0)):
                continue
            t = text_of(pm.group(1))
            if t:
                positioned.append((pm.start(), {"type": "paragraph", "text": t}))
        for lm in RE_LI.finditer(inner):
            t = text_of(lm.group(1))
            if t and len(t) < 2000:
                positioned.append((lm.start(), {"type": "listitem", "text": t}))
        positioned.sort(key=lambda x: x[0])
        blocks.extend(b for _, b in positioned)
    return blocks


# ------------------------------------------------------- shape 2: lessons list
def extract_lessons(doc: str) -> list[dict]:
    cards: list[dict] = []
    for item in RE_SPLIT_GRID.split(doc)[1:]:
        tm = re.search(
            r'<h4[^>]*class="[^"]*grid-title[^"]*"[^>]*>\s*<a[^>]*href="([^"]+)"[^>]*>(.*?)</a>',
            item, re.S,
        ) or re.search(r'<h4[^>]*>\s*<a[^>]*href="([^"]+)"[^>]*>(.*?)</a>', item, re.S)
        if not tm:
            continue
        title = text_of(tm.group(2))
        if not title:
            continue
        yt = RE_YT_THUMB.search(item)
        cats = [text_of(c) for c in re.findall(
            r'<li class="lesson-category">\s*<a[^>]*>(.*?)</a>', item, re.S)]
        dm = re.search(r'<div class="grid-desc">(.*?)</div>', item, re.S)
        im = RE_IMG_SRC.search(item)
        am = RE_IMG_ALT.search(item)
        cards.append({
            "title": title,
            "href": tm.group(1),
            "categories": [c.strip() for c in cats if c.strip()],
            "description": text_of(dm.group(1)) if dm else "",
            "youtubeId": yt.group(1) if yt else None,
            "thumb": im.group(1) if im else None,
            "alt": html.unescape(am.group(1)) if am else title,
        })
    return cards


def extract_lesson_categories(doc: str) -> list[dict]:
    out: list[dict] = []
    m = re.search(r'<nav aria-label="categories">(.*?)</nav>', doc, re.S)
    if not m:
        return out
    for a in re.finditer(r'<a[^>]*href="([^"]+)"[^>]*>(.*?)</a>', m.group(1), re.S):
        t = text_of(a.group(2))
        if t:
            out.append({"label": t, "href": a.group(1)})
    return out


# -------------------------------------------------- shape 3: blog collection
def extract_blog(doc: str) -> list[dict]:
    cards: list[dict] = []
    for item in RE_SPLIT_BLOG.split(doc)[1:]:
        tm = re.search(
            r'<h1[^>]*class="[^"]*blog-title[^"]*"[^>]*>\s*<a[^>]*href="([^"]+)"[^>]*>(.*?)</a>',
            item, re.S,
        )
        if not tm:
            continue
        am = re.search(r'<span class="blog-author">(.*?)</span>', item, re.S)
        dm = re.search(r'<time[^>]*class="blog-date"[^>]*>(.*?)</time>', item, re.S)
        em = re.search(r'<div class="blog-excerpt-wrapper">(.*?)</div>', item, re.S)
        alm = RE_IMG_ALT.search(item)
        img = None
        for tag in re.finditer(r"<img[^>]*>", item, re.I):
            cand = best_image(tag.group(0))
            if cand:
                img = cand
        cards.append({
            "title": text_of(tm.group(2)),
            "href": tm.group(1),
            "author": text_of(am.group(1)) if am else "",
            "date": text_of(dm.group(1)) if dm else "",
            "excerpt": text_of(em.group(1)) if em else "",
            "image": img,
            "alt": html.unescape(alm.group(1)) if alm else text_of(tm.group(2)),
        })
    return cards


# ------------------------------------------------------------- page metadata
def extract_meta(doc: str) -> dict:
    out: dict = {}
    for key, pat in (
        ("title", r"<title>(.*?)</title>"),
        ("description",
         r'<meta\s+name=["\']description["\'][^>]*content=["\'](.*?)["\']'),
        ("ogImage",
         r'<meta\s+property=["\']og:image["\'][^>]*content=["\'](.*?)["\']'),
    ):
        m = re.search(pat, doc, re.S | re.I)
        if m:
            out[key] = html.unescape(m.group(1)).strip()
    return out


def extract_hero(doc: str) -> str | None:
    """Fluid pages render a section-background image; used as the hero."""
    m = re.search(r'<div class="section-background">(.*?)</div>', doc, re.S)
    if m:
        for tag in re.finditer(r"<img[^>]*>", m.group(1), re.I):
            u = best_image(tag.group(0))
            if u:
                return u
    return None


# ------------------------------------------------------------- detail pages
def extract_video_item(doc: str, path: str) -> dict:
    cfg = re.search(r'data-config-embed-video="(.*?)"\s*>', doc, re.S)
    yt_id = None
    if cfg:
        blob = html.unescape(cfg.group(1))
        m = RE_YT_EMBED.search(blob)
        if m:
            yt_id = m.group(1)
    if not yt_id:
        m = RE_YT_THUMB.search(doc)
        yt_id = m.group(1) if m else None

    tm = re.search(r'<h2[^>]*class="lesson-details-title"[^>]*>(.*?)</h2>', doc, re.S)
    title = text_of(tm.group(1)) if tm else ""

    cats = [text_of(c) for c in re.findall(
        r'<li class="lesson-category">\s*<a[^>]*>(.*?)</a>', doc, re.S)]

    dm = re.search(r'<div class="lesson-details-description"[^>]*>(.*?)</div>\s*</div>',
                   doc, re.S)
    desc = text_of(dm.group(1)) if dm else ""

    related = []
    for rm in re.finditer(
        r'<a[^>]*class="related-item-link[^"]*"[^>]*href="([^"]+)"[^>]*>(.*?)</a>',
        doc, re.S,
    ):
        related.append({"href": rm.group(1), "title": text_of(rm.group(2))})

    return {
        "type": "video",
        "slug": path.strip("/").replace("/", "--"),
        "path": path,
        "title": title,
        "categories": [c.strip() for c in cats if c.strip()],
        "description": desc,
        "youtubeId": yt_id,
        "related": related,
        "meta": extract_meta(doc),
    }


def extract_article_item(doc: str, path: str) -> dict:
    """Blog detail post: title, author, date, rich-text body."""
    tm = re.search(r'<title>(.*?)</title>', doc, re.S)
    title = html.unescape(tm.group(1)).split("&mdash;")[0].strip() if tm else ""

    am = re.search(r'<span class="blog-author">(.*?)</span>', doc, re.S)
    dm = re.search(r'<time[^>]*>(.*?)</time>', doc, re.S)

    # the article body lives inside the main-content wrapper
    body_html = ""
    bm = re.search(
        r'data-content-field="main-content"[^>]*>(.*?)(?:<div class="blog-more-link|</article>)',
        doc, re.S,
    )
    if bm:
        body_html = bm.group(1)
    else:
        chunks = RE_SQS_HTML.findall(doc)
        body_html = "\n".join(chunks)

    # keep block structure: headings, paragraphs, lists, images
    body: list[dict] = []
    for tag in re.finditer(
        r"<(h[1-6]|p|li|blockquote)\b[^>]*>(.*?)</\1>", body_html, re.S | re.I
    ):
        t = text_of(tag.group(2))
        if not t:
            continue
        name = tag.group(1).lower()
        if name.startswith("h"):
            body.append({"type": "heading", "level": int(name[1]), "text": t})
        elif name == "li":
            body.append({"type": "listitem", "text": t})
        elif name == "blockquote":
            body.append({"type": "quote", "text": t})
        else:
            body.append({"type": "paragraph", "text": t})

    images: list[str] = []
    for tag in re.finditer(r"<img[^>]*>", body_html, re.I):
        u = best_image(tag.group(0))
        if u and u not in images:
            images.append(u)

    return {
        "type": "article",
        "slug": path.strip("/").replace("/", "--"),
        "path": path,
        "title": title,
        "author": text_of(am.group(1)) if am else "",
        "date": text_of(dm.group(1)) if dm else "",
        "body": dedupe(body),
        "images": images,
        "meta": extract_meta(doc),
    }


# --------------------------------------------------------------------- main
def main() -> int:
    src = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
    outdir = Path(sys.argv[2] if len(sys.argv) > 2 else "content")
    pages_dir = outdir / "pages"
    items_dir = outdir / "items"
    pages_dir.mkdir(parents=True, exist_ok=True)
    items_dir.mkdir(parents=True, exist_ok=True)

    manifest: dict[str, dict] = {}
    detail_dir = src / "detail"

    for filename, slug, navtitle, path, kind in PAGES:
        f = src / filename
        if not f.exists():
            print(f"  ! missing {filename}")
            continue
        doc = f.read_text(encoding="utf-8", errors="ignore")

        payload: dict = {
            "slug": slug, "navTitle": navtitle, "path": path, "kind": kind,
            "source": f"https://www.atlasofshenzhen.cn/{path}",
            "meta": extract_meta(doc),
        }
        if kind == "fluid":
            payload["blocks"] = dedupe(extract_fluid(doc))
            payload["heroImage"] = extract_hero(doc)
        elif kind == "lessons":
            payload["cards"] = extract_lessons(doc)
            payload["categories"] = extract_lesson_categories(doc)
            payload["blocks"] = dedupe(extract_fluid(doc))
        else:
            payload["cards"] = extract_blog(doc)
            payload["blocks"] = dedupe(extract_fluid(doc))

        (pages_dir / f"{slug}.json").write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )

        # ---- detail items referenced by this page's cards
        n_detail = 0
        for card in payload.get("cards", []):
            href = card.get("href", "")
            if not href:
                continue
            df = detail_dir / (href.strip("/").replace("/", "__") + ".html")
            if not df.exists():
                continue
            ddoc = df.read_text(encoding="utf-8", errors="ignore")
            if kind == "lessons":
                item = extract_video_item(ddoc, href)
                # Some detail pages omit the description; the list card has it.
                if not item.get("description") and card.get("description"):
                    item["description"] = card["description"]
                if not item.get("youtubeId") and card.get("youtubeId"):
                    item["youtubeId"] = card["youtubeId"]
                if not item.get("title") and card.get("title"):
                    item["title"] = card["title"]
                card["detailSlug"] = item["slug"]
            else:
                item = extract_article_item(ddoc, href)
                # Prefer a clean card title over the "Title — brand" <title> tag.
                if card.get("title"):
                    item["title"] = card["title"]
                if not item.get("author") and card.get("author"):
                    item["author"] = card["author"]
                card["detailSlug"] = item["slug"]
            (items_dir / (item["slug"] + ".json")).write_text(
                json.dumps(item, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            n_detail += 1

        # rewrite page file now that cards carry detailSlug
        (pages_dir / f"{slug}.json").write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )

        manifest[slug] = {
            "kind": kind,
            "blocks": len(payload.get("blocks", [])),
            "cards": len(payload.get("cards", [])),
            "details": n_detail,
        }
        print(f"  {slug:18s} kind={kind:8s} blocks={manifest[slug]['blocks']:3d} "
              f"cards={manifest[slug]['cards']:3d} details={n_detail:3d}")

    (outdir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"\n{len(manifest)} pages | "
          f"{sum(v['cards'] for v in manifest.values())} cards | "
          f"{sum(v['details'] for v in manifest.values())} detail items")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
