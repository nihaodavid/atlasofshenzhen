/**
 * Calendar access layer.
 *
 * Reads content/calendar/events.json — the English-language events calendar.
 * Like lib/content.ts, everything is read at build time so the page is
 * statically rendered; there is no runtime data fetching.
 *
 * Data provenance matters here: these listings are extracted from Chinese
 * event posters (mostly Xiaohongshu), so each event carries a `confidence`
 * map and a `flags` array recording what still needs human verification.
 */
import { readFileSync } from "node:fs";
import { join } from "node:path";

const CALENDAR_DIR = join(process.cwd(), "content", "calendar");
const EVENTS_FILE = join(CALENDAR_DIR, "events.json");

/** How confident the extraction is, per field. */
export type Confidence = "HIGH" | "MEDIUM" | "LOW";

export type PriceType = "free" | "free_entry_paid_extras" | "paid";

export type Category =
  | "food"
  | "coffee"
  | "market"
  | "family"
  | "music"
  | "exhibition"
  | "crafts";

export interface SubEvent {
  title_en: string;
  /** ISO date, YYYY-MM-DD. */
  date: string;
  times?: string[];
  note?: string;
}

export interface CalendarEvent {
  id: string;
  slug: string;
  title_en: string;
  title_zh?: string;
  subtitle_en?: string;
  /** ISO date, YYYY-MM-DD — inclusive. */
  start: string;
  /** ISO date, YYYY-MM-DD — inclusive. */
  end: string;
  /** Opening hours within each day, e.g. "11:00–21:00". Null = all day. */
  daily_time?: string | null;
  venue_en: string;
  venue_zh?: string;
  district?: string;
  price_type: PriceType;
  price_note?: string | null;
  categories: Category[];
  summary_en?: string;
  highlights_en?: string[];
  organiser?: string;
  source?: string;
  confidence?: { date: Confidence; venue: Confidence; price: Confidence };
  flags?: string[];
  sub_events?: SubEvent[];
}

interface EventsFile {
  generated: string;
  verified_on: string;
  source_note: string;
  events: CalendarEvent[];
}

let cache: EventsFile | null = null;

function load(): EventsFile {
  if (cache) return cache;
  cache = JSON.parse(readFileSync(EVENTS_FILE, "utf-8")) as EventsFile;
  return cache;
}

export function getAllEvents(): CalendarEvent[] {
  return load().events;
}

/** The date the listings were last checked against their sources. */
export function getVerifiedOn(): string {
  return load().verified_on;
}

/** Human-readable provenance line, shown under the page intro. */
export function getSourceNote(): string {
  return load().source_note;
}

export function getEvent(slug: string): CalendarEvent | undefined {
  return load().events.find((e) => e.slug === slug);
}

/* ------------------------------------------------------------------
   Date helpers.

   IMPORTANT: never derive a calendar day with toISOString(). These dates
   are plain YYYY-MM-DD strings with no timezone, and `toISOString()` on a
   locally-parsed Date converts to UTC — which shifts every date back a day
   in UTC+n zones (China is UTC+8) and forward a day in UTC−n zones.
   Formatting the local Date parts is the only correct way here.
   ------------------------------------------------------------------ */

/** Parse "YYYY-MM-DD" as local midnight. */
export function toDate(iso: string): Date {
  const [y, m, d] = iso.split("-").map(Number);
  return new Date(y, m - 1, d);
}

/** Local YYYY-MM-DD key. The safe counterpart to toISOString().slice(0,10). */
export function dayKey(d: Date): string {
  const p = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}`;
}

/* ------------------------------------------------------------------
   iCal (RFC 5545) — the open subscription standard, consumed by Apple
   Calendar, Google Calendar and Outlook. Stable UIDs mean subscribers
   get updates to the same event rather than duplicates.
   ------------------------------------------------------------------ */

/** Escape a text value per RFC 5545 §3.3.11. */
function icsEscape(text: string): string {
  return text
    .replace(/\\/g, "\\\\")
    .replace(/;/g, "\\;")
    .replace(/,/g, "\\,")
    .replace(/\r?\n/g, "\\n");
}

/**
 * Fold a content line to 75 octets per RFC 5545 §3.1. Continuation lines
 * begin with a single space. Counted in UTF-8 octets, not characters, so
 * multi-byte text is split safely at a character boundary.
 *
 * Pass the COMPLETE line including its property name — folding the value on
 * its own and prepending "DESCRIPTION:" afterwards pushes the first line over
 * the limit by exactly the length of the prefix.
 */
function icsFold(line: string): string {
  const bytes = Buffer.from(line, "utf-8");
  if (bytes.length <= 75) return line;

  const out: string[] = [];
  let current = "";
  let currentBytes = 0;
  // 75 for the first line, 74 for continuations (which spend one octet on the
  // leading space).
  let limit = 75;

  for (const ch of line) {
    const size = Buffer.byteLength(ch, "utf-8");
    if (currentBytes + size > limit) {
      out.push(current);
      current = ch;
      currentBytes = size;
      limit = 74;
    } else {
      current += ch;
      currentBytes += size;
    }
  }
  out.push(current);
  return out.join("\r\n ");
}

/** Escape a value and fold the COMPLETE line, name included. */
function icsLine(name: string, value: string): string {
  return icsFold(`${name}:${icsEscape(value)}`);
}

/**
 * All-day event dates use VALUE=DATE. DTEND is exclusive per the spec, so a
 * single-day event on the 4th ends on the 5th; a 1–4 Oct run ends 5 Oct.
 */
function icsDateAdd(iso: string, days: number): string {
  const d = toDate(iso);
  d.setDate(d.getDate() + days);
  return dayKey(d).replace(/-/g, "");
}

const CRLF = "\r\n";

export function buildIcs(events: CalendarEvent[], siteUrl: string): string {
  const stamp = new Date()
    .toISOString()
    .replace(/[-:]/g, "")
    .replace(/\.\d{3}/, "");

  const lines: string[] = [
    "BEGIN:VCALENDAR",
    "VERSION:2.0",
    "PRODID:-//Atlas of Shenzhen//Events Calendar//EN",
    "CALSCALE:GREGORIAN",
    "METHOD:PUBLISH",
    "X-WR-CALNAME:What's on in Shenzhen",
    icsLine(
      "X-WR-CALDESC",
      "An English-language calendar of food festivals, markets, exhibitions and pop-ups across Shenzhen."
    ),
    "X-WR-TIMEZONE:Asia/Shanghai",
  ];

  for (const e of events) {
    const url = `${siteUrl}/calendar/${e.slug}/`;
    const description = [
      e.subtitle_en,
      e.summary_en,
      e.price_note ? `Note: ${e.price_note}` : null,
      e.organiser ? `Organiser: ${e.organiser}` : null,
      `Details: ${url}`,
    ]
      .filter(Boolean)
      .join("\n\n");

    const isMultiDay = e.start !== e.end;

    lines.push(
      "BEGIN:VEVENT",
      `UID:${e.id}@atlasofshenzhen.online`,
      `DTSTAMP:${stamp}`,
      `DTSTART;VALUE=DATE:${e.start.replace(/-/g, "")}`,
      // DTEND is exclusive; a one-day event ends the next day.
      `DTEND;VALUE=DATE:${icsDateAdd(e.end, 1)}`,
      icsLine("SUMMARY", e.title_en),
      icsLine("DESCRIPTION", description),
      icsLine(
        "LOCATION",
        [e.venue_en, e.district, "Shenzhen"].filter(Boolean).join(", ")
      ),
      `URL:${url}`,
      `CATEGORIES:${e.categories.map((c) => c.toUpperCase()).join(",")}`,
      // Seed all-day events to free/busy=transparent so subscribing does not
      // block the user's working hours for a festival they may not attend.
      "TRANSP:TRANSPARENT",
      `X-ATLAS-DAYS:${isMultiDay ? "multi" : "single"}`,
      "END:VEVENT"
    );
  }

  lines.push("END:VCALENDAR");
  return lines.join(CRLF) + CRLF;
}
