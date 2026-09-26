/**
 * Content access layer.
 *
 * Reads the JSON produced by scripts/extract.py and exposes typed helpers.
 * Astro reads these at build time, so the whole site is statically rendered.
 */
import { readFileSync, readdirSync } from "node:fs";
import { join } from "node:path";

const CONTENT_DIR = join(process.cwd(), "content");
const PAGES_DIR = join(CONTENT_DIR, "pages");
const ITEMS_DIR = join(CONTENT_DIR, "items");

export interface Block {
  type: "heading" | "paragraph" | "listitem" | "quote";
  level?: number;
  text: string;
}

export interface Card {
  title: string;
  href: string;
  categories?: string[];
  description?: string;
  youtubeId?: string | null;
  thumb?: string | null;
  image?: string | null;
  alt?: string;
  author?: string;
  date?: string;
  excerpt?: string;
  detailSlug?: string;
}

export interface PageDoc {
  slug: string;
  navTitle: string;
  path: string;
  kind: "fluid" | "lessons" | "blog";
  meta: { title?: string; description?: string; ogImage?: string };
  blocks: Block[];
  cards?: Card[];
  categories?: { label: string; href: string }[];
  heroImage?: string | null;
}

export interface ItemDoc {
  type: "video" | "article";
  slug: string;
  path: string;
  title: string;
  categories?: string[];
  description?: string;
  youtubeId?: string | null;
  related?: { href: string; title: string }[];
  author?: string;
  date?: string;
  body?: Block[];
  images?: string[];
  meta: { title?: string; description?: string; ogImage?: string };
}

function readJson<T>(path: string): T {
  return JSON.parse(readFileSync(path, "utf-8")) as T;
}

export function getPage(slug: string): PageDoc {
  return readJson<PageDoc>(join(PAGES_DIR, `${slug}.json`));
}

export function getAllPages(): PageDoc[] {
  return readdirSync(PAGES_DIR)
    .filter((f) => f.endsWith(".json"))
    .map((f) => readJson<PageDoc>(join(PAGES_DIR, f)));
}

export function getItem(slug: string): ItemDoc {
  return readJson<ItemDoc>(join(ITEMS_DIR, `${slug}.json`));
}

export function getAllItems(): ItemDoc[] {
  return readdirSync(ITEMS_DIR)
    .filter((f) => f.endsWith(".json"))
    .map((f) => readJson<ItemDoc>(join(ITEMS_DIR, f)));
}

/** Items of a given slug prefix that belong to one collection page. */
export function getItemsFor(prefix: string): ItemDoc[] {
  return getAllItems().filter((i) => i.slug.startsWith(prefix + "--"));
}

/**
 * The original site used `<collection>/<slug>` URLs. Astro emits directory
 * pages, so we mirror the same shape with a trailing slash.
 */
export function itemUrl(item: ItemDoc): string {
  const [collection] = item.path.replace(/^\//, "").split("/");
  return `/${collection}/${item.slug}/`;
}
