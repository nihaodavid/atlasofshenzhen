# The Atlas of Shenzhen

A static rebuild of **atlasofshenzhen.online**, migrated off Squarespace onto
Astro so the whole site is plain HTML/CSS that can be hosted for free on Vercel
and version-controlled on GitHub.

- **Production:** <https://atlasofshenzhen.online>
- **Repository:** <https://github.com/nihaodavid/atlasofshenzhen>
- **Legacy site:** <https://www.atlasofshenzhen.cn> (original Squarespace)

---

## What was migrated

| | Count |
|---|---|
| Main pages | 12 |
| Video entries | 40 (each with its own detail page) |
| Article entries | 18 (books, history, nature, service, manufacturers) |
| Generated pages | 71 |
| Build output | ~1.7 MB, fully static |

Every original URL is preserved exactly, so no existing link or search result
breaks:

```
/aboutthis/  /team/  /faq/  /join-us/  /future-works-1/
/history/    /books/ /nature/ /service/ /manufacturers-1/
/videos/     /videos/v/<id>/
/history/<post>/   /books/<post>/   /service/<post>/   ...
```

---

## Quick start

```bash
npm install          # install dependencies
npm run dev          # local dev server  -> http://localhost:4321
npm run build        # static build      -> dist/
npm run preview      # preview the build
```

Requires Node.js **>= 20** (developed on 22.22.2).

---

## Project structure

```
atlas-of-shenzhen/
├── content/                  # migrated content (JSON, generated)
│   ├── pages/                # one file per main page
│   ├── items/                # one file per video / article
│   └── manifest.json         # inventory + counts
├── scripts/
│   ├── crawl.py              # mirror source pages  (step 1)
│   ├── extract.py            # HTML -> structured JSON (step 2)
│   └── gen_pages.py          # regenerate page wrappers
├── src/
│   ├── components/           # Hero, CardGrid, YouTubeLite, ContentBlocks
│   ├── layouts/              # Base, FluidPage, Collection
│   ├── lib/content.ts        # typed content access layer
│   ├── pages/                # routes (file-based)
│   ├── styles/global.css     # design tokens + base styles
│   └── site.config.ts        # site name, nav, palette  <- edit me
├── public/
│   ├── images/               # logo, hero artwork, OG image
│   ├── _redirects            # legacy URL map (Netlify/Cloudflare)
│   └── favicon.svg
├── vercel.json               # Vercel build + headers + redirects
└── design-tokens.md          # colours / fonts sampled from the original
```

---

## Content pipeline

The `content/` JSON is committed, so normal development never touches the
scrapers. Re-run them only if the source site changes:

```bash
# 1. mirror the source pages + detail pages
python scripts/crawl.py <links.txt> <crawl_dir>

# 2. convert to structured JSON
python scripts/extract.py <crawl_dir> content
```

Both scripts are plain Python 3 with no third-party dependencies.

---

## Design decisions worth knowing

**Colour.** The brand teal `#4AA3B0` was sampled directly from the original
hero PNG — 96% of that image's pixels are exactly this value. The white
line-art flower was extracted from the same image by keying out the teal and
saved as `public/images/hero-flower.webp`.

**Typography.** The original site uses the Adobe Typekit face *gopher*, whose
licence is bound to the Squarespace account and **cannot be re-hosted** on the
new site. `Manrope` (free, Google Fonts, metrically similar) is used instead.
To restore the exact original face, buy a Typekit/Adobe Fonts licence and swap
the `<link>` in `src/layouts/BaseLayout.astro`.

**Videos.** The original `/videos` page showed 40 YouTube thumbnails with **no
working player**. This rebuild adds real detail pages with click-to-play
embeds (`YouTubeLite.astro`): the iframe is only injected after a deliberate
click, which avoids loading ~1 MB of player JavaScript on every page view.

**Images.** Content images still point at `images.squarespace-cdn.com` (as
agreed, media migration was deferred). See *Next steps* below.

---

## Next steps

- [ ] **Localise images.** 228 images are still served from the Squarespace
      CDN, which will break if that account lapses. Add them to
      `public/images/` and rewrite the URLs in `content/`.
- [ ] **Restore the exact typeface** if a Typekit licence is available.
- [ ] **Point the old .cn domain** at the new site with 301 redirects so
      existing inbound links and search ranking carry over.
- [ ] Add `alt` text to content images (the original had none — an a11y and
      SEO win waiting to happen).

---

## Deployment

See [`DEPLOY.md`](./DEPLOY.md) for the full GitHub → Vercel walkthrough,
including the zero-downtime DNS switch.
