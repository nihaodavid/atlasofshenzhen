"""
Generate the simple listing / content pages as .astro files.

These pages are thin wrappers: each imports a layout and passes the
extracted content through. Keeping them as explicit files (rather than a
single dynamic route) means each page can be tuned independently later,
and the URLs stay readable on disk.

Run:  python scripts/gen_pages.py
"""

from __future__ import annotations

import sys
from pathlib import Path

OUT = Path("src/pages")

# (slug, component, title, fallback description, hero heading)
COLLECTIONS = [
    ("history", "CollectionLayout", "History",
     "Long-form research on the places, railways, villages and industries "
     "that shaped Shenzhen.", "History"),
    ("books", "CollectionLayout", "Books",
     "Reading notes and reviews on Shenzhen, its libraries, publishers and "
     "reading culture.", "Books"),
    ("nature", "CollectionLayout", "Nature",
     "Shenzhen\u2019s coastline, parks, birds and plants \u2014 field notes "
     "from the city\u2019s wilder edges.", "Nature"),
    ("service", "CollectionLayout", "Service",
     "Sector briefings on logistics, manufacturing, education and "
     "sustainable development.", "Service"),
    ("manufacturers-1", "CollectionLayout", "Manufacturers",
     "A directory of manufacturers and industrial clusters across Shenzhen "
     "and the Greater Bay Area.", "Manufacturers"),
]

FLUID = [
    ("aboutthis", "FluidPageLayout", "Vision & Mission",
     "The Atlas of Shenzhen is a comprehensive and innovative statement "
     "concerning the geography, history and industrial prospects of the city "
     "of Shenzhen.", "Vision & Mission"),
    ("team", "FluidPageLayout", "Team",
     "Meet the researchers, writers, translators and designers behind the "
     "Atlas of Shenzhen.", "Team"),
    ("faq", "FluidPageLayout", "FAQ",
     "Answers to common questions about the Atlas of Shenzhen, our research "
     "process, and how to contribute.", "Frequently Asked Questions"),
    ("join-us", "FluidPageLayout", "Join Us",
     "Contribute writing, photography, translation or research to the Atlas "
     "of Shenzhen.", "Join Us"),
    ("future-works-1", "FluidPageLayout", "Future Works",
     "The maps, archives and publications we are building next for the Atlas "
     "of Shenzhen.", "Future Works"),
]

COLLECTION_TEMPLATE = '''---
import {component} from "../layouts/{component}.astro";
import {{ getPage }} from "../lib/content";

const page = getPage("{slug}");
---

<{component}
  slug="{slug}"
  title="{title}"
  description={{page.meta.description || "{desc}"}}
  heroHeading="{heading}"
  cards={{page.cards ?? []}}
  blocks={{page.blocks}}
/>
'''

FLUID_TEMPLATE = '''---
import {component} from "../layouts/{component}.astro";
import {{ getPage }} from "../lib/content";

const page = getPage("{slug}");
---

<{component}
  slug="{slug}"
  title="{title}"
  description={{page.meta.description || "{desc}"}}
  heroHeading="{heading}"
  blocks={{page.blocks}}
/>
'''


def write_page(template: str, row: tuple[str, str, str, str, str]) -> None:
    slug, component, title, desc, heading = row
    # Escape any double quotes inside the fallback description.
    safe_desc = desc.replace('"', '\\"')
    body = template.format(
        slug=slug, component=component, title=title,
        desc=safe_desc, heading=heading,
    )
    path = OUT / f"{slug}.astro"
    path.write_text(body, encoding="utf-8")
    print(f"  wrote {path}")


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    print("Generating collection pages:")
    for row in COLLECTIONS:
        write_page(COLLECTION_TEMPLATE, row)
    print("Generating content pages:")
    for row in FLUID:
        write_page(FLUID_TEMPLATE, row)
    print(f"\nDone: {len(COLLECTIONS) + len(FLUID)} pages")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
