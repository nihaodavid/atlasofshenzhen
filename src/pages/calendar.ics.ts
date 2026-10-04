/**
 * /calendar.ics — subscribable iCal feed.
 *
 * Pre-rendered at build time alongside the HTML, so subscribers can add
 * https://atlasofshenzhen.online/calendar.ics to Apple Calendar, Google
 * Calendar or Outlook and get updates on each deploy.
 *
 * Only events that have not finished are included: a subscription feed that
 * accumulates years of dead entries is worse than useless in a calendar app.
 */
import type { APIRoute } from "astro";
import { getAllEvents, buildIcs, toDate, dayKey } from "../lib/calendar";

export const prerender = true;

export const GET: APIRoute = () => {
  const today = dayKey(new Date());
  const t = toDate(today);

  const live = getAllEvents().filter((e) => toDate(e.end) >= t);

  const body = buildIcs(live, "https://atlasofshenzhen.online");

  return new Response(body, {
    headers: {
      "Content-Type": "text/calendar; charset=utf-8",
      "Content-Disposition": 'inline; filename="shenzhen-events.ics"',
      "Cache-Control": "public, max-age=3600",
    },
  });
};
