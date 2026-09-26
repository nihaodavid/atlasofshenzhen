import { defineConfig } from "astro/config";
import sitemap from "@astrojs/sitemap";

// Canonical production origin.
export const SITE = "https://atlasofshenzhen.online";

export default defineConfig({
  site: SITE,
  // Fully static output — deployable to Vercel / Cloudflare Pages / any CDN.
  output: "static",
  integrations: [sitemap()],
  build: {
    // Emit /videos/index.html rather than /videos.html so the URLs match
    // the original Squarespace permalinks exactly (important for SEO).
    format: "directory",
  },
  image: {
    // Images are served from /public/images (see scripts/fetch_media.py).
    // Sharp handles optimisation at build time.
    service: { entrypoint: "astro/assets/services/sharp" },
  },
  trailingSlash: "ignore",
});
