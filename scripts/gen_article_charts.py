"""
Generate brand-styled SVG charts for the Atlas of Shenzhen article
"Shenzhen and the AI Short-Drama Boom".

All figures are taken verbatim from the article body so the charts and the
prose can never drift apart.

Output: public/images/service/ai-short-drama-shenzhen-<nn>-<name>.svg
Palette follows design-tokens.md (brand teal #4AA3B0).
"""

import os
import html

TEAL = "#4AA3B0"
TEAL_D = "#2F7F8C"   # darker teal for emphasis
TEAL_L = "#A8D5DC"   # light teal
INK = "#272727"
INK_SOFT = "#3E3E3E"
MUTED = "#6B6B6B"
GRID = "#E7E7E7"
SURFACE = "#F6F6F6"
WHITE = "#FFFFFF"
ACCENT = "#D97757"   # warm accent for "highlight" marks

FONT = "Manrope, 'Helvetica Neue', Arial, sans-serif"
OUT_DIR = os.path.join("public", "images", "service")

W = 1200
H = 675
PAD_L = 90
PAD_R = 70
PAD_T = 130
PAD_B = 100


def esc(s):
    return html.escape(str(s))


def header(title, subtitle):
    """Common chart header: title + subtitle."""
    return f"""
  <text x="{PAD_L}" y="60" font-family="{FONT}" font-size="34" font-weight="600" fill="{INK}">{esc(title)}</text>
  <text x="{PAD_L}" y="96" font-family="{FONT}" font-size="19" font-weight="400" fill="{MUTED}">{esc(subtitle)}</text>
"""


def footer(src):
    return f"""
  <text x="{PAD_L}" y="{H - 34}" font-family="{FONT}" font-size="15" fill="{MUTED}">Source: {esc(src)}</text>
  <text x="{W - PAD_R}" y="{H - 34}" text-anchor="end" font-family="{FONT}" font-size="15" fill="{MUTED}">Atlas of Shenzhen</text>
"""


def svg_open(bg=WHITE):
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img">
  <rect width="{W}" height="{H}" fill="{bg}"/>"""


def write(name, body, bg=WHITE):
    os.makedirs(OUT_DIR, exist_ok=True)
    path = os.path.join(OUT_DIR, name)
    with open(path, "w", encoding="utf-8") as f:
        f.write(svg_open(bg) + body + "\n</svg>\n")
    print(f"  wrote {path} ({os.path.getsize(path)} bytes)")


# ---------------------------------------------------------------- chart 1
def chart_market_growth():
    """Grouped bars: 2025 -> 2026 market size, with 138% growth callout."""
    title = "A market that grew 138% in a single year"
    sub = "China's AI drama & AI anime-drama sector, market size (RMB bn)"

    plot_y = PAD_T + 60
    plot_h = 330
    base_y = plot_y + plot_h
    gmax = 45.0

    def yv(v):
        return base_y - (v / gmax) * plot_h

    parts = [header(title, sub), footer("DataEye, brokerage research, Sep 2026")]

    # horizontal gridlines
    for g in range(0, 46, 10):
        y = yv(g)
        parts.append(
            f'  <line x1="{PAD_L}" y1="{y:.1f}" x2="{W - PAD_R}" y2="{y:.1f}" '
            f'stroke="{GRID}" stroke-width="1"/>'
        )
        parts.append(
            f'  <text x="{PAD_L - 16}" y="{y + 6:.1f}" text-anchor="end" '
            f'font-family="{FONT}" font-size="16" fill="{MUTED}">{g}</text>'
        )

    # baseline
    parts.append(
        f'  <line x1="{PAD_L}" y1="{base_y}" x2="{W - PAD_R}" y2="{base_y}" '
        f'stroke="{INK_SOFT}" stroke-width="2"/>'
    )

    bars = [
        ("2025", 16.8, "explosion year", TEAL_L),
        ("2026 forecast", 40.0, "projected", TEAL),
    ]
    bw = 150
    gap = 210
    x0 = PAD_L + 130

    for i, (label, val, note, color) in enumerate(bars):
        x = x0 + i * (bw + gap)
        y = yv(val)
        h = base_y - y
        parts.append(
            f'  <rect x="{x:.1f}" y="{y:.1f}" width="{bw}" height="{h:.1f}" '
            f'rx="6" fill="{color}"/>'
        )
        parts.append(
            f'  <text x="{x + bw/2:.1f}" y="{y - 16:.1f}" text-anchor="middle" '
            f'font-family="{FONT}" font-size="30" font-weight="600" fill="{INK}">¥{val:.1f}bn</text>'
        )
        parts.append(
            f'  <text x="{x + bw/2:.1f}" y="{base_y + 32:.1f}" text-anchor="middle" '
            f'font-family="{FONT}" font-size="20" font-weight="600" fill="{INK_SOFT}">{esc(label)}</text>'
        )
        parts.append(
            f'  <text x="{x + bw/2:.1f}" y="{base_y + 58:.1f}" text-anchor="middle" '
            f'font-family="{FONT}" font-size="16" fill="{MUTED}">{esc(note)}</text>'
        )

    # growth callout between bars
    cx = (x0 + bw + (x0 + bw + gap)) / 2
    cy = base_y - plot_h * 0.62
    parts.append(
        f'  <path d="M{x0+bw+16:.1f},{base_y - plot_h*0.30:.1f} L{cx:.1f},{cy:.1f} '
        f'L{x0+bw+gap-16:.1f},{base_y - plot_h*0.72:.1f}" fill="none" '
        f'stroke="{ACCENT}" stroke-width="2.5" stroke-dasharray="7 5"/>'
    )
    parts.append(
        f'  <text x="{cx:.1f}" y="{cy - 14:.1f}" text-anchor="middle" '
        f'font-family="{FONT}" font-size="24" font-weight="600" fill="{ACCENT}">+138%</text>'
    )

    # Jan-May 2026 annotation
    parts.append(
        f'  <text x="{PAD_L}" y="{PAD_T + 18}" font-family="{FONT}" font-size="18" '
        f'fill="{INK_SOFT}">Jan–May 2026 alone had already booked <tspan font-weight="600">¥22bn</tspan></text>'
    )
    return "".join(parts)


# ---------------------------------------------------------------- chart 2
def chart_viewers():
    """Line: deduplicated short-drama users in China, 5 points."""
    title = "851 million viewers, and the arithmetic of attention"
    sub = "Deduplicated short-drama users in China (millions)"

    pts = [
        ("Jun 2024", 576),
        ("Dec 2024", 662),
        ("Jun 2025", 696),
        ("Feb 2026", 718),
        ("May 2026", 851),
    ]
    plot_y = PAD_T + 50
    plot_h = 300
    base_y = plot_y + plot_h
    ymin, ymax = 500, 900

    def yv(v):
        return base_y - ((v - ymin) / (ymax - ymin)) * plot_h

    xs = [PAD_L + 60 + i * ((W - PAD_L - PAD_R - 120) / (len(pts) - 1)) for i in range(len(pts))]

    parts = [header(title, sub), footer("QuestMobile, cited in the article")]

    for g in range(500, 901, 100):
        y = yv(g)
        parts.append(
            f'  <line x1="{PAD_L}" y1="{y:.1f}" x2="{W - PAD_R}" y2="{y:.1f}" '
            f'stroke="{GRID}" stroke-width="1"/>'
        )
        parts.append(
            f'  <text x="{PAD_L - 16}" y="{y + 6:.1f}" text-anchor="end" '
            f'font-family="{FONT}" font-size="16" fill="{MUTED}">{g}</text>'
        )

    parts.append(
        f'  <line x1="{PAD_L}" y1="{base_y}" x2="{W - PAD_R}" y2="{base_y}" '
        f'stroke="{INK_SOFT}" stroke-width="2"/>'
    )

    # area fill under the line
    area_pts = " ".join(f"{x:.1f},{yv(v):.1f}" for x, (_, v) in zip(xs, pts))
    parts.append(
        f'  <polygon points="{xs[0]:.1f},{base_y} {area_pts} {xs[-1]:.1f},{base_y}" '
        f'fill="{TEAL}" opacity="0.13"/>'
    )
    # the line
    line_pts = " ".join(f"{x:.1f},{yv(v):.1f}" for x, (_, v) in zip(xs, pts))
    parts.append(
        f'  <polyline points="{line_pts}" fill="none" stroke="{TEAL}" '
        f'stroke-width="4" stroke-linejoin="round" stroke-linecap="round"/>'
    )

    for x, (label, v) in zip(xs, pts):
        y = yv(v)
        is_last = v == 851
        r = 10 if is_last else 7
        parts.append(
            f'  <circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="{WHITE}" '
            f'stroke="{TEAL_D if is_last else TEAL}" stroke-width="4"/>'
        )
        parts.append(
            f'  <text x="{x:.1f}" y="{y - 26:.1f}" text-anchor="middle" '
            f'font-family="{FONT}" font-size="20" font-weight="600" fill="{INK}">{v}</text>'
        )
        parts.append(
            f'  <text x="{x:.1f}" y="{base_y + 34:.1f}" text-anchor="middle" '
            f'font-family="{FONT}" font-size="16" fill="{MUTED}">{esc(label)}</text>'
        )

    # annotation
    parts.append(
        f'  <text x="{W - PAD_R}" y="{PAD_T + 22}" text-anchor="end" font-family="{FONT}" '
        f'font-size="18" fill="{INK_SOFT}">≈67% of China\'s active mobile internet users</text>'
    )
    return "".join(parts)


# ---------------------------------------------------------------- chart 3
def chart_supply():
    """Donut: format split of AI photorealistic / 2D / 3D / other."""
    title = "More than 95% of everything new is AI"
    sub = "Q1 2026 AI short-drama releases by format (128,000 titles went online; ~122,000 were AI)"

    cx, cy, r = W / 2 - 130, H / 2 + 30, 175
    import math

    slices = [
        ("AI photorealistic", 56, TEAL_D),
        ("2D animation", 35, "#8FCDD6"),
        ("3D animation", 5, "#C9E4E8"),
        ("Other formats", 4, "#D8D8D8"),
    ]

    parts = [header(title, sub), footer("Q1 2026 release data, Sep 2026")]

    start = -90.0
    for label, pct, color in slices:
        sweep = pct / 100.0 * 360.0
        end = start + sweep
        x1 = cx + r * math.cos(math.radians(start))
        y1 = cy + r * math.sin(math.radians(start))
        x2 = cx + r * math.cos(math.radians(end))
        y2 = cy + r * math.sin(math.radians(end))
        large = 1 if sweep > 180 else 0
        parts.append(
            f'  <path d="M{cx:.1f},{cy:.1f} L{x1:.1f},{y1:.1f} '
            f'A{r},{r} 0 {large} 1 {x2:.1f},{y2:.1f} Z" fill="{color}"/>'
        )
        start = end

    # donut hole
    parts.append(f'  <circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r*0.55:.1f}" fill="{WHITE}"/>')
    parts.append(
        f'  <text x="{cx:.1f}" y="{cy - 12:.1f}" text-anchor="middle" font-family="{FONT}" '
        f'font-size="46" font-weight="600" fill="{TEAL_D}">95%+</text>'
    )
    parts.append(
        f'  <text x="{cx:.1f}" y="{cy + 24:.1f}" text-anchor="middle" font-family="{FONT}" '
        f'font-size="17" fill="{MUTED}">AI-produced</text>'
    )

    # legend
    lx = cx + r + 80
    ly = cy - 105
    for label, pct, color in slices:
        parts.append(f'  <rect x="{lx}" y="{ly}" width="26" height="26" rx="5" fill="{color}"/>')
        parts.append(
            f'  <text x="{lx + 42}" y="{ly + 20}" font-family="{FONT}" font-size="21" '
            f'font-weight="600" fill="{INK}">{pct}%</text>'
        )
        parts.append(
            f'  <text x="{lx + 105}" y="{ly + 20}" font-family="{FONT}" font-size="19" '
            f'fill="{INK_SOFT}">{esc(label)}</text>'
        )
        ly += 54

    return "".join(parts)


# ---------------------------------------------------------------- chart 4
def chart_hit_rate():
    """Dot matrix: 1,000 dots, 1 highlighted => under 1% hit rate."""
    title = "The 1% problem"
    sub = "H1 2026: 221,900 new AI short dramas on Douyin — only 1,055 passed 100 million plays"

    cols, rows = 50, 20
    total = cols * rows  # 1,000 dots
    dot_r = 5
    grid_w = 900
    grid_x = (W - grid_w) / 2
    grid_y = PAD_T + 45
    step_x = grid_w / (cols - 1)
    step_y = 17.5

    parts = [header(title, sub), footer("Douyin release data, H1 2026")]

    # one highlighted dot, positioned deterministically
    hot_index = 13 * cols + 31  # arbitrary but stable

    for i in range(total):
        c = i % cols
        r = i // cols
        x = grid_x + c * step_x
        y = grid_y + r * step_y
        if i == hot_index:
            parts.append(
                f'  <circle cx="{x:.1f}" cy="{y:.1f}" r="{dot_r + 6}" fill="{ACCENT}" opacity="0.22"/>'
            )
            parts.append(f'  <circle cx="{x:.1f}" cy="{y:.1f}" r="{dot_r}" fill="{ACCENT}"/>')
        else:
            parts.append(
                f'  <circle cx="{x:.1f}" cy="{y:.1f}" r="{dot_r - 2:.1f}" fill="#D5D5D5"/>'
            )

    # leader line to the highlighted dot + label
    hx = grid_x + (hot_index % cols) * step_x
    hy = grid_y + (hot_index // cols) * step_y
    lab_x = hx + 120
    parts.append(
        f'  <line x1="{hx + dot_r + 8:.1f}" y1="{hy:.1f}" x2="{lab_x - 12:.1f}" y2="{hy:.1f}" '
        f'stroke="{ACCENT}" stroke-width="2"/>'
    )
    parts.append(
        f'  <text x="{lab_x:.1f}" y="{hy - 10:.1f}" font-family="{FONT}" font-size="21" '
        f'font-weight="600" fill="{ACCENT}">&lt; 1% hit rate</text>'
    )
    parts.append(
        f'  <text x="{lab_x:.1f}" y="{hy + 16:.1f}" font-family="{FONT}" font-size="16" '
        f'fill="{MUTED}">≈1 breakout per 1,000 titles</text>'
    )
    # caption below the grid, clear of the footer
    cap_y = grid_y + (rows - 1) * step_y + 40
    parts.append(
        f'  <text x="{grid_x}" y="{cap_y:.1f}" font-family="{FONT}" '
        f'font-size="16" fill="{MUTED}">Each dot ≈ 222 titles — the grey field represents 1,000</text>'
    )
    return "".join(parts)


# ---------------------------------------------------------------- chart 5
def chart_bars_timeline():
    """Horizontal timeline of video-model releases 2023-2026.

    Twelve releases are laid out chronologically along a single axis; labels
    alternate above and below the line so they never overlap each other.
    """
    title = "The cost collapse"
    sub = "Video-generation model releases that made AI drama viable"

    events = [
        ("Mar 2023", "Midjourney V5", "photographic realism"),
        ("Nov 2023", "Pika 1.0", "lightweight diffusion"),
        ("Feb 2024", "Sora", "OpenAI entry"),
        ("Aug 2024", "Kling 1.0", "first public DiT model"),
        ("Apr 2025", "Kling 2.0", ""),
        ("Sep 2025", "Sora 2", ""),
        ("Feb 2026", "Seedance 2.0", "character anchoring"),
        ("Feb 2026", "Kling 3.0", "unified workflow"),
        ("Mar 2026", "SkyReels V4", ""),
        ("Apr 2026", "HappyHorse", "Alibaba"),
        ("Jul 2026", "MiniMax H3", ""),
        ("Aug 2026", "Wan 3.0", "30s single shot"),
    ]

    parts = [header(title, sub), footer("Vendor release dates, as reported")]

    axis_y = PAD_T + 165
    x_start = PAD_L + 45
    x_end = W - PAD_R - 45
    n = len(events)
    step = (x_end - x_start) / (n - 1)

    # time axis
    parts.append(
        f'  <line x1="{x_start - 20}" y1="{axis_y}" x2="{x_end + 20}" y2="{axis_y}" '
        f'stroke="{INK_SOFT}" stroke-width="2.5"/>'
    )

    for i, (date, name, note) in enumerate(events):
        x = x_start + i * step
        above = (i % 2 == 0)
        # emphasise the 2026 cluster that unlocked full-story video
        hot = name in ("Seedance 2.0", "Kling 3.0")
        color = ACCENT if hot else TEAL
        dot_r = 9 if hot else 7

        # tick + dot on the axis
        parts.append(
            f'  <line x1="{x:.1f}" y1="{axis_y - 13}" x2="{x:.1f}" y2="{axis_y + 13}" '
            f'stroke="{color}" stroke-width="2.5"/>'
        )
        parts.append(f'  <circle cx="{x:.1f}" cy="{axis_y:.1f}" r="{dot_r}" fill="{color}"/>')

        if above:
            # stem up, then label block stacked upward
            parts.append(
                f'  <line x1="{x:.1f}" y1="{axis_y - 13}" x2="{x:.1f}" y2="{axis_y - 52}" '
                f'stroke="{color}" stroke-width="1.5" opacity="0.55"/>'
            )
            parts.append(
                f'  <text x="{x:.1f}" y="{axis_y - 96}" text-anchor="middle" font-family="{FONT}" '
                f'font-size="16" fill="{MUTED}">{esc(date)}</text>'
            )
            parts.append(
                f'  <text x="{x:.1f}" y="{axis_y - 70}" text-anchor="middle" font-family="{FONT}" '
                f'font-size="19" font-weight="600" fill="{color if hot else INK}">{esc(name)}</text>'
            )
            if note:
                parts.append(
                    f'  <text x="{x:.1f}" y="{axis_y - 122}" text-anchor="middle" '
                    f'font-family="{FONT}" font-size="14" fill="{MUTED}">{esc(note)}</text>'
                )
        else:
            parts.append(
                f'  <line x1="{x:.1f}" y1="{axis_y + 13}" x2="{x:.1f}" y2="{axis_y + 52}" '
                f'stroke="{color}" stroke-width="1.5" opacity="0.55"/>'
            )
            parts.append(
                f'  <text x="{x:.1f}" y="{axis_y + 76}" text-anchor="middle" font-family="{FONT}" '
                f'font-size="16" fill="{MUTED}">{esc(date)}</text>'
            )
            parts.append(
                f'  <text x="{x:.1f}" y="{axis_y + 102}" text-anchor="middle" font-family="{FONT}" '
                f'font-size="19" font-weight="600" fill="{INK}">{esc(name)}</text>'
            )
            if note:
                parts.append(
                    f'  <text x="{x:.1f}" y="{axis_y + 126}" text-anchor="middle" '
                    f'font-family="{FONT}" font-size="14" fill="{MUTED}">{esc(note)}</text>'
                )

    # cost callout, bottom-left, clear of the axis labels
    parts.append(
        f'  <text x="{PAD_L}" y="{axis_y + 190}" font-family="{FONT}" font-size="19" fill="{INK_SOFT}">'
        f'A single AI short-drama episode now costs a few thousand yuan —</text>'
    )
    parts.append(
        f'  <text x="{PAD_L}" y="{axis_y + 222}" font-family="{FONT}" font-size="25" '
        f'font-weight="600" fill="{TEAL_D}">an 80–90% cut against live-action production</text>'
    )
    return "".join(parts)


if __name__ == "__main__":
    print("Generating charts...")
    write("ai-short-drama-shenzhen-10-market.svg", chart_market_growth())
    write("ai-short-drama-shenzhen-11-viewers.svg", chart_viewers())
    write("ai-short-drama-shenzhen-12-supply.svg", chart_supply())
    write("ai-short-drama-shenzhen-13-hitrate.svg", chart_hit_rate())
    write("ai-short-drama-shenzhen-14-timeline.svg", chart_bars_timeline())
    print("Done.")
