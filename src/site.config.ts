/**
 * Site-wide configuration.
 *
 * `NAV` mirrors the original Squarespace navigation exactly so that migrated
 * URLs and labels stay identical (important for SEO and for returning users).
 */

export const SITE = {
  name: "The Atlas of Shenzhen",
  shortName: "Atlas of Shenzhen",
  /** New production domain (replaces the original .cn domain). */
  url: "https://atlasofshenzhen.online",
  /** Kept for reference / redirects from the original Squarespace site. */
  legacyUrl: "https://www.atlasofshenzhen.cn",
  email: "info@atlasofshenzhen.cn",
  address: ["Yuehai District", "Shenzhen, CN"],
  locale: "en",
  description:
    "Atlas of Shenzhen offers comprehensive, authentic, and up-to-date information about Shenzhen — including neighbourhoods, transport, culture, business, and practical travel tips for residents and visitors.",
} as const;

export type NavItem = {
  label: string;
  href: string;
  children?: NavItem[];
};

export const NAV: NavItem[] = [
  { label: "Home", href: "/" },
  { label: "Videos", href: "/videos/" },
  {
    label: "About",
    href: "/aboutthis/",
    children: [
      { label: "Vision & Mission", href: "/aboutthis/" },
      { label: "Team", href: "/team/" },
      { label: "FAQ", href: "/faq/" },
      { label: "Join Us", href: "/join-us/" },
    ],
  },
  {
    label: "Opinions",
    href: "/future-works-1/",
    children: [
      { label: "Future Works", href: "/future-works-1/" },
      { label: "History", href: "/history/" },
      { label: "Books", href: "/books/" },
      { label: "Manufacturers", href: "/manufacturers-1/" },
      { label: "Service", href: "/service/" },
      { label: "Nature", href: "/nature/" },
    ],
  },
];

/** Brand palette, sampled from the original site (see design-tokens.md). */
export const BRAND = {
  teal: "#4AA3B0",
  ink: "#272727",
  inkSoft: "#3E3E3E",
  surface: "#F6F6F6",
  border: "#DDDDDD",
  white: "#FFFFFF",
} as const;
