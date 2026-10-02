/**
 * schema.org builders.
 *
 * Keeping the JSON-LD shapes here (rather than inline in every page) means
 * the @id / url conventions are defined once and stay consistent — which
 * matters because Google reconciles entities across pages by @id.
 */
import { SITE } from "../site.config";

export const ORG_ID = `${SITE.url}/#organization`;
export const WEBSITE_ID = `${SITE.url}/#website`;

/** Stable absolute URL for a site-relative path. */
export function abs(path = "/"): string {
  return new URL(path, SITE.url).href;
}

/** The publishing organisation — referenced by @id from other nodes. */
export function organization() {
  return {
    "@type": "Organization",
    "@id": ORG_ID,
    name: SITE.name,
    alternateName: SITE.shortName,
    url: SITE.url,
    email: SITE.email,
    logo: {
      "@type": "ImageObject",
      url: abs("/images/logo.jpg"),
      width: 150,
      height: 71,
    },
    address: {
      "@type": "PostalAddress",
      addressLocality: "Shenzhen",
      addressRegion: "Guangdong",
      addressCountry: "CN",
    },
    sameAs: [SITE.legacyUrl],
  };
}

/** Site-level node; declares the site name Google shows in results. */
export function website() {
  return {
    "@type": "WebSite",
    "@id": WEBSITE_ID,
    url: SITE.url,
    name: SITE.name,
    description: SITE.description,
    inLanguage: SITE.locale,
    publisher: { "@id": ORG_ID },
  };
}

/** Emitted on every page. */
export function siteGraph() {
  return {
    "@context": "https://schema.org",
    "@graph": [organization(), website()],
  };
}

export function breadcrumbs(trail: { name: string; path: string }[]) {
  return {
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    itemListElement: trail.map((step, i) => ({
      "@type": "ListItem",
      position: i + 1,
      name: step.name,
      item: abs(step.path),
    })),
  };
}

/** A collection listing page (e.g. /videos/) — improves sitelink eligibility. */
export function collectionPage(opts: {
  name: string;
  description: string;
  path: string;
}) {
  return {
    "@context": "https://schema.org",
    "@type": "CollectionPage",
    name: opts.name,
    description: opts.description,
    url: abs(opts.path),
    isPartOf: { "@id": WEBSITE_ID },
    publisher: { "@id": ORG_ID },
  };
}

export function videoObject(opts: {
  name: string;
  description: string;
  path: string;
  youtubeId: string | null;
  uploadDate?: string;
  thumbnail?: string;
}) {
  const thumbnailUrl =
    opts.thumbnail ??
    (opts.youtubeId
      ? `https://i.ytimg.com/vi/${opts.youtubeId}/maxresdefault.jpg`
      : abs("/images/og-default.jpg"));

  const node: Record<string, unknown> = {
    "@context": "https://schema.org",
    "@type": "VideoObject",
    name: opts.name,
    description: opts.description,
    thumbnailUrl: [thumbnailUrl],
    url: abs(opts.path),
    publisher: { "@id": ORG_ID },
    // Required by Google for video rich results. The migration did not carry
    // per-video publish dates, so fall back to the site launch date rather
    // than omit the field entirely (which blocks eligibility).
    uploadDate: opts.uploadDate ?? "2021-01-01T00:00:00+08:00",
    isPartOf: { "@id": WEBSITE_ID },
  };

  if (opts.youtubeId) {
    node.embedUrl = `https://www.youtube.com/embed/${opts.youtubeId}`;
    node.contentUrl = `https://www.youtube.com/watch?v=${opts.youtubeId}`;
  }

  return node;
}

/** FAQPage — drives expandable Q&A directly in search results. */
export function faqPage(qa: { question: string; answer: string }[]) {
  return {
    "@context": "https://schema.org",
    "@type": "FAQPage",
    mainEntity: qa.map(({ question, answer }) => ({
      "@type": "Question",
      name: question,
      acceptedAnswer: { "@type": "Answer", text: answer },
    })),
  };
}

/** Article — for blog-style collection entries (history, books, service…). */
export function article(opts: {
  headline: string;
  description: string;
  path: string;
  image?: string;
  datePublished?: string;
}) {
  return {
    "@context": "https://schema.org",
    "@type": "Article",
    headline: opts.headline,
    description: opts.description,
    url: abs(opts.path),
    mainEntityOfPage: abs(opts.path),
    publisher: { "@id": ORG_ID },
    author: { "@id": ORG_ID },
    datePublished: opts.datePublished ?? "2021-01-01T00:00:00+08:00",
    ...(opts.image ? { image: [opts.image] } : {}),
    isPartOf: { "@id": WEBSITE_ID },
  };
}

/**
 * Derives FAQ Q&A pairs from the extracted content blocks: a heading starts a
 * question, the paragraphs until the next heading form its answer.
 */
export function faqPairsFromBlocks(
  blocks: { type: string; level?: number; text: string }[],
): { question: string; answer: string }[] {
  const pairs: { question: string; answer: string }[] = [];
  let question: string | null = null;
  let answer: string[] = [];

  const flush = () => {
    if (question && answer.length > 0) {
      pairs.push({ question, answer: answer.join(" ") });
    }
    answer = [];
  };

  for (const block of blocks) {
    if (block.type === "heading") {
      flush();
      question = block.text;
      continue;
    }
    if (question && (block.type === "paragraph" || block.type === "listitem")) {
      answer.push(block.text);
    }
  }
  flush();

  // Skip the page's own title heading (it isn't a question) and any pair whose
  // "answer" is just the shared contact footer.
  return pairs
    .filter((p) => !/^frequently asked questions$/i.test(p.question))
    .filter((p) => !/^info@atlasofshenzhen\.cn\s*Yuehai District/i.test(p.answer));
}
