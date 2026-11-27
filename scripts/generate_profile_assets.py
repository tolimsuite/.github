#!/usr/bin/env python3
"""Generate the TOLIM organization profile assets from GitHub data."""

import base64
import html
import json
import math
import os
import sys
import urllib.error
import urllib.request
from collections import Counter
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

ORG = os.environ.get("GITHUB_ORG", "tolimsuite")
API = os.environ.get("GITHUB_API_URL", "https://api.github.com").rstrip("/")
TOKEN = os.environ.get("GITHUB_TOKEN", "").strip()
OUT = Path(__file__).resolve().parent.parent / "profile" / "assets"
EXCLUDED_REPOS = {".github", ".github-private"}
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
FONT = "-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif"

THEMES = {
    "light": {
        "card": "#f6f8fa",
        "border": "#d0d7de",
        "text": "#1f2328",
        "muted": "#656d76",
        "accent": "#0969da",
        "accent2": "#8250df",
        "glow1": "#38bdf8",
        "glow2": "#a78bfa",
        "hero_from": "#eef6ff",
        "hero_to": "#f7f2ff",
        "levels": ["#eaeef2", "#ccfbf1", "#5eead4", "#14b8a6", "#0f766e"],
    },
    "dark": {
        "card": "#161b22",
        "border": "#30363d",
        "text": "#e6edf3",
        "muted": "#8b949e",
        "accent": "#58a6ff",
        "accent2": "#bc8cff",
        "glow1": "#22d3ee",
        "glow2": "#8b5cf6",
        "hero_from": "#0b1220",
        "hero_to": "#171326",
        "levels": ["#21262d", "#0f3d3a", "#115e59", "#14b8a6", "#5eead4"],
    },
}

LANG_COLORS = {
    "Java": "#b07219",
    "Kotlin": "#A97BFF",
    "Python": "#3572A5",
    "TypeScript": "#3178c6",
    "JavaScript": "#f1e05a",
    "Go": "#00ADD8",
    "Rust": "#dea584",
    "Shell": "#89e051",
    "C": "#555555",
    "C++": "#f34b7d",
    "C#": "#178600",
    "HTML": "#e34c26",
    "CSS": "#563d7c",
    "Ruby": "#701516",
    "Scala": "#c22d40",
    "Swift": "#F05138",
    "PHP": "#4F5D95",
    "Vue": "#41b883",
    "Dockerfile": "#384d54",
    "Groovy": "#4298b8",
    "Other": "#8b949e",
}
FALLBACK_COLORS = ["#6e7681", "#58a6ff", "#3fb950", "#d29922", "#f85149", "#a371f7"]


def headers():
    return {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {TOKEN}",
        "User-Agent": "tolim-profile-assets",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def get_json(url):
    request = urllib.request.Request(url, headers=headers())
    with urllib.request.urlopen(request, timeout=30) as response:
        body = response.read()
        return (json.loads(body.decode("utf-8")) if body else None), response.headers


def get_paged(path):
    url = f"{API}{path}"
    items = []
    while url:
        data, response_headers = get_json(url)
        if isinstance(data, list):
            items.extend(data)
        elif data is not None:
            items.append(data)
        if data is None:
            break
        next_url = None
        for part in (response_headers.get("Link") or "").split(","):
            if 'rel="next"' in part:
                next_url = part.split(";")[0].strip().strip("<>")
        url = next_url
    return items


def fetch_repos():
    repos = get_paged(f"/orgs/{ORG}/repos?per_page=100&type=public&sort=updated")
    return [repo for repo in repos if not repo.get("fork") and repo["name"] not in EXCLUDED_REPOS]


def fetch_languages(repo):
    data, _ = get_json(f"{API}/repos/{ORG}/{repo}/languages")
    return data or {}


def fetch_commits(repo, since):
    commits = []
    for page in range(1, 21):
        url = (
            f"{API}/repos/{ORG}/{repo}/commits?since={since.isoformat()}T00:00:00Z"
            f"&per_page=100&page={page}"
        )
        try:
            data, _ = get_json(url)
        except urllib.error.HTTPError as error:
            if error.code in (404, 409):
                break
            raise
        if not isinstance(data, list) or not data:
            break
        commits.extend(data)
        if len(data) < 100:
            break
    return commits


def fetch_contributors(repos):
    counts = Counter()
    for repo in repos:
        try:
            data = get_paged(f"/repos/{ORG}/{repo}/contributors?per_page=100")
            for item in data or []:
                login = item.get("login")
                if login and not login.endswith("[bot]"):
                    counts[login] += int(item.get("contributions", 0))
        except Exception as error:
            print(f"contributors {repo}: {error}", file=sys.stderr)
    return counts


def fetch_avatar(name, size=96):
    url = f"https://github.com/{name}.png?size={size}"
    try:
        request = urllib.request.Request(url, headers={"User-Agent": "tolim-profile-assets"})
        with urllib.request.urlopen(request, timeout=30) as response:
            return base64.b64encode(response.read()).decode("ascii")
    except Exception as error:
        print(f"avatar {name}: {error}", file=sys.stderr)
        return None


def commit_date(commit):
    for key in ("author", "committer"):
        value = (commit.get("commit", {}).get(key) or {}).get("date")
        if value:
            return date.fromisoformat(value[:10])
    return None


def level(count):
    if count <= 0:
        return 0
    if count <= 2:
        return 1
    if count <= 5:
        return 2
    if count <= 9:
        return 3
    return 4


def svg_start(width, height, label):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-label="{label}">'
    )


def accent_defs(theme):
    return (
        '<defs><linearGradient id="accent" x1="0%" y1="0%" x2="100%" y2="0%">'
        f'<stop offset="0%" stop-color="{theme["accent"]}"/>'
        f'<stop offset="100%" stop-color="{theme["accent2"]}"/>'
        "</linearGradient></defs>"
    )


def font_style():
    return f"<style>text{{font-family:{FONT};}}</style>"


def card_rect(theme, width, height):
    return (
        f'<rect x="0.75" y="0.75" width="{width - 1.5}" height="{height - 1.5}" rx="18" '
        f'fill="{theme["card"]}" stroke="url(#accent)" stroke-width="1.5"/>'
    )


def section_title(theme, title, subtitle):
    return (
        f'<text x="24" y="34" font-size="17" font-weight="700" fill="{theme["text"]}">{title}</text>'
        f'<text x="24" y="54" font-size="11" fill="{theme["muted"]}">{subtitle}</text>'
    )


def hero_svg(theme, avatar):
    width, height = 1000, 260
    parts = [
        svg_start(width, height, "TOLIM Technologies"),
        "<defs>",
        f'<linearGradient id="hero-bg" x1="0%" y1="0%" x2="100%" y2="100%">'
        f'<stop offset="0%" stop-color="{theme["hero_from"]}"/>'
        f'<stop offset="100%" stop-color="{theme["hero_to"]}"/></linearGradient>',
        f'<linearGradient id="accent" x1="0%" y1="0%" x2="100%" y2="0%">'
        f'<stop offset="0%" stop-color="{theme["accent"]}"/>'
        f'<stop offset="55%" stop-color="{theme["accent2"]}"/>'
        f'<stop offset="100%" stop-color="{theme["accent"]}"/></linearGradient>',
        '<filter id="blur"><feGaussianBlur stdDeviation="30"/></filter>',
        f'<pattern id="dots" width="24" height="24" patternUnits="userSpaceOnUse">'
        f'<circle cx="1.5" cy="1.5" r="1.2" fill="{theme["text"]}" opacity="0.10"/></pattern>',
        f'<clipPath id="hero-clip"><rect width="{width}" height="{height}" rx="24"/></clipPath>',
        '<clipPath id="avatar-clip"><circle cx="140" cy="130" r="66"/></clipPath>',
        "</defs>",
        font_style(),
        f'<rect width="{width}" height="{height}" rx="24" fill="url(#hero-bg)" stroke="{theme["border"]}"/>',
        '<g clip-path="url(#hero-clip)">',
        f'<rect width="{width}" height="{height}" fill="url(#dots)"/>',
        f'<circle cx="900" cy="20" r="150" fill="{theme["glow1"]}" opacity="0.18" filter="url(#blur)"/>',
        f'<circle cx="760" cy="260" r="170" fill="{theme["glow2"]}" opacity="0.15" filter="url(#blur)"/>',
        f'<text x="980" y="250" text-anchor="end" font-size="220" font-weight="800" '
        f'fill="{theme["text"]}" opacity="0.04">T</text>',
        "</g>",
        f'<circle cx="140" cy="130" r="74" fill="none" stroke="url(#accent)" stroke-width="3"/>',
    ]
    if avatar:
        parts.append(
            f'<image x="74" y="64" width="132" height="132" href="data:image/png;base64,{avatar}" '
            f'clip-path="url(#avatar-clip)" preserveAspectRatio="xMidYMid slice"/>'
        )
    else:
        parts.append(f'<circle cx="140" cy="130" r="66" fill="url(#accent)"/>')
        parts.append(
            f'<text x="140" y="147" text-anchor="middle" font-size="46" font-weight="700" '
            f'fill="{theme["card"]}">T</text>'
        )
    parts += [
        f'<text x="240" y="110" font-size="42" font-weight="700" fill="url(#accent)" '
        f'letter-spacing="-1">TOLIM Technologies</text>',
        f'<text x="240" y="149" font-size="17" fill="{theme["text"]}">'
        "Secure by design. Delivered with care.</text>",
        f'<text x="240" y="177" font-size="15" fill="{theme["muted"]}">安全设计，可靠交付。</text>',
        f'<rect x="240" y="199" width="210" height="28" rx="14" fill="{theme["card"]}" '
        f'stroke="{theme["border"]}"/>',
        f'<text x="345" y="218" text-anchor="middle" font-size="10" letter-spacing="1.6" '
        f'fill="{theme["muted"]}">SECURE BY DESIGN</text>',
        "</svg>",
    ]
    return "\n".join(parts)


def stats_svg(theme, stats):
    width, height = 1000, 140
    cards = [
        ("REPOSITORIES · 仓库", stats["repos"], theme["accent"]),
        ("COMMITS · 提交", stats["commits"], theme["accent2"]),
        ("LANGUAGES · 语言", stats["languages"], theme["glow1"]),
        ("CONTRIBUTORS · 贡献者", stats["contributors"], theme["glow2"]),
    ]
    parts = [
        svg_start(width, height, "TOLIM organization statistics"),
        accent_defs(theme),
        font_style(),
    ]
    card_width, gap, top, card_height = 235, 10, 10, 120
    for index, (label, value, color) in enumerate(cards):
        x = 10 + index * (card_width + gap)
        parts.append(
            f'<rect x="{x + 0.75}" y="{top + 0.75}" width="{card_width - 1.5}" '
            f'height="{card_height - 1.5}" rx="16" fill="{theme["card"]}" '
            f'stroke="url(#accent)" stroke-width="1.5"/>'
        )
        parts.append(f'<rect x="{x + 20}" y="{top + 22}" width="34" height="4" rx="2" fill="{color}"/>')
        parts.append(
            f'<text x="{x + 20}" y="{top + 72}" font-size="36" font-weight="700" '
            f'fill="{theme["text"]}">{value:,}</text>'
        )
        parts.append(
            f'<text x="{x + 20}" y="{top + 99}" font-size="10.5" letter-spacing="1.1" '
            f'fill="{theme["muted"]}">{label}</text>'
        )
    parts.append("</svg>")
    return "\n".join(parts)


def heatmap_svg(counts, theme):
    width, height = 1000, 230
    today = datetime.now(timezone.utc).date()
    start = today - timedelta(days=364)
    start -= timedelta(days=(start.weekday() + 1) % 7)
    weeks = ((today - start).days // 7) + 1

    cell, gap, step = 11, 3, 14
    grid_width = weeks * step
    grid_x = (width - grid_width) // 2
    grid_y = 82

    parts = [
        svg_start(width, height, "Commit activity across TOLIM repositories over the last 12 months"),
        accent_defs(theme),
        font_style(),
        card_rect(theme, width, height),
        section_title(theme, "Commit activity", "Last 12 months · 最近 12 个月"),
        f'<rect x="850" y="20" width="126" height="24" rx="12" fill="{theme["card"]}" '
        f'stroke="{theme["border"]}"/>',
        f'<text x="913" y="36" text-anchor="middle" font-size="9" letter-spacing="1.2" '
        f'fill="{theme["muted"]}">AUTO-UPDATED</text>',
    ]

    last_label_x = -100
    for week in range(weeks):
        for day in range(7):
            current = start + timedelta(days=week * 7 + day)
            if current.day == 1 and current <= today:
                x = grid_x + week * step + cell / 2
                if x - last_label_x >= 30:
                    parts.append(
                        f'<text x="{x:.1f}" y="72" text-anchor="middle" font-size="10" '
                        f'fill="{theme["muted"]}">{MONTHS[current.month - 1]}</text>'
                    )
                    last_label_x = x

    for row, label in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        parts.append(
            f'<text x="{grid_x - 12}" y="{grid_y + row * step + cell - 1}" text-anchor="end" '
            f'font-size="10" fill="{theme["muted"]}">{label}</text>'
        )

    for week in range(weeks):
        for day in range(7):
            current = start + timedelta(days=week * 7 + day)
            count = counts.get(current, 0) if current <= today else 0
            fill = theme["levels"][level(count)]
            x = grid_x + week * step
            y = grid_y + day * step
            title = ""
            if current <= today:
                suffix = "s" if count != 1 else ""
                title = f"<title>{current.isoformat()}: {count} commit{suffix}</title>"
            parts.append(
                f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" rx="3" '
                f'fill="{fill}">{title}</rect>'
            )

    legend_y = 194
    legend_x = 850
    parts.append(
        f'<text x="{legend_x - 8}" y="{legend_y + 10}" text-anchor="end" font-size="10" '
        f'fill="{theme["muted"]}">Less</text>'
    )
    for index in range(5):
        parts.append(
            f'<rect x="{legend_x + index * step}" y="{legend_y}" width="{cell}" height="{cell}" '
            f'rx="3" fill="{theme["levels"][index]}"/>'
        )
    parts.append(
        f'<text x="{legend_x + 5 * step + 6}" y="{legend_y + 10}" font-size="10" '
        f'fill="{theme["muted"]}">More</text>'
    )
    parts.append("</svg>")
    return "\n".join(parts)


def language_svg(lang_bytes, theme):
    width, height = 1000, 280
    items = sorted(lang_bytes.items(), key=lambda item: item[1], reverse=True)
    top = items[:6]
    other = sum(value for _, value in items[6:])
    if other:
        top.append(("Other", other))
    total = sum(value for _, value in top)

    cx, cy, radius, stroke = 190, 170, 78, 26
    circumference = 2 * math.pi * radius

    parts = [
        svg_start(width, height, "Language distribution across TOLIM repositories"),
        accent_defs(theme),
        font_style(),
        card_rect(theme, width, height),
        section_title(theme, "Languages", "Across all repositories · 全部仓库"),
        f'<circle cx="{cx}" cy="{cy}" r="{radius}" fill="none" stroke="{theme["border"]}" '
        f'stroke-width="{stroke}" opacity="0.45"/>',
    ]

    if total:
        parts.append(f'<g transform="rotate(-90 {cx} {cy})">')
        offset = 0.0
        for index, (name, value) in enumerate(top):
            share = value / total
            gap = 2 if len(top) > 1 else 0
            dash = max(share * circumference - gap, 0.5)
            color = LANG_COLORS.get(name, FALLBACK_COLORS[index % len(FALLBACK_COLORS)])
            percentage = share * 100
            parts.append(
                f'<circle cx="{cx}" cy="{cy}" r="{radius}" fill="none" stroke="{color}" '
                f'stroke-width="{stroke}" stroke-dasharray="{dash:.2f} {circumference - dash:.2f}" '
                f'stroke-dashoffset="{-offset:.2f}"><title>{html.escape(name)}: '
                f"{percentage:.1f}%</title></circle>"
            )
            offset += share * circumference
        parts.append("</g>")
        parts.append(
            f'<text x="{cx}" y="{cy - 2}" text-anchor="middle" font-size="40" font-weight="700" '
            f'fill="{theme["text"]}">{len(lang_bytes)}</text>'
        )
        parts.append(
            f'<text x="{cx}" y="{cy + 22}" text-anchor="middle" font-size="9.5" '
            f'letter-spacing="1.4" fill="{theme["muted"]}">LANGUAGES · 语言</text>'
        )
        for index, (name, value) in enumerate(top):
            y = 92 + index * 26
            color = LANG_COLORS.get(name, FALLBACK_COLORS[index % len(FALLBACK_COLORS)])
            percentage = value / total * 100
            parts.append(f'<rect x="350" y="{y - 10}" width="12" height="12" rx="3" fill="{color}"/>')
            parts.append(
                f'<text x="372" y="{y}" font-size="13" fill="{theme["text"]}">'
                f"{html.escape(name)}</text>"
            )
            parts.append(
                f'<text x="960" y="{y}" text-anchor="end" font-size="12" '
                f'fill="{theme["muted"]}">{percentage:.1f}%</text>'
            )
    else:
        parts.append(
            f'<text x="{cx}" y="{cy}" text-anchor="middle" font-size="14" '
            f'fill="{theme["muted"]}">No language data yet</text>'
        )

    parts.append("</svg>")
    return "\n".join(parts)


def contributors_svg(theme, contributions, avatars):
    width, height = 1000, 240
    shown = contributions.most_common(26)
    size, gap, per_row, start_x, start_y = 56, 16, 13, 24, 84
    step = size + gap

    positions = []
    for index, (login, count) in enumerate(shown):
        col = index % per_row
        row = index // per_row
        cx = start_x + size // 2 + col * step
        cy = start_y + size // 2 + row * step
        positions.append((index, login, count, cx, cy))

    defs = [
        "<defs>",
        '<linearGradient id="accent" x1="0%" y1="0%" x2="100%" y2="0%">'
        f'<stop offset="0%" stop-color="{theme["accent"]}"/>'
        f'<stop offset="100%" stop-color="{theme["accent2"]}"/></linearGradient>',
    ]
    for index, login, count, cx, cy in positions:
        defs.append(
            f'<clipPath id="avatar-{index}"><circle cx="{cx}" cy="{cy}" '
            f'r="{size // 2}"/></clipPath>'
        )
    defs.append("</defs>")

    parts = [
        svg_start(width, height, "TOLIM contributors"),
        "\n".join(defs),
        font_style(),
        card_rect(theme, width, height),
        section_title(theme, "Contributors", "Across all repositories · 全部仓库"),
    ]

    if positions:
        for index, login, count, cx, cy in positions:
            parts.append(f'<g><title>{html.escape(login)} · {count} contributions</title>')
            parts.append(
                f'<circle cx="{cx}" cy="{cy}" r="{size // 2 + 2}" fill="none" '
                f'stroke="url(#accent)" stroke-width="1.5" opacity="0.8"/>'
            )
            avatar = avatars.get(login)
            if avatar:
                parts.append(
                    f'<image x="{cx - size // 2}" y="{cy - size // 2}" width="{size}" '
                    f'height="{size}" href="data:image/png;base64,{avatar}" '
                    f'clip-path="url(#avatar-{index})" preserveAspectRatio="xMidYMid slice"/>'
                )
            else:
                parts.append(
                    f'<circle cx="{cx}" cy="{cy}" r="{size // 2}" fill="{theme["card"]}" '
                    f'stroke="{theme["border"]}"/>'
                )
                parts.append(
                    f'<text x="{cx}" y="{cy + 5}" text-anchor="middle" font-size="18" '
                    f'fill="{theme["muted"]}">{html.escape(login[:1].upper())}</text>'
                )
            parts.append("</g>")
        if len(contributions) > len(shown):
            parts.append(
                f'<text x="{width - 24}" y="{height - 14}" text-anchor="end" font-size="10" '
                f'fill="{theme["muted"]}">+{len(contributions) - len(shown)} more</text>'
            )
    else:
        parts.append(
            f'<text x="24" y="100" font-size="13" fill="{theme["muted"]}">'
            "Contributors will appear here.</text>"
        )

    parts.append("</svg>")
    return "\n".join(parts)


def write_if_changed(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.read_text(encoding="utf-8") == content:
        print(f"unchanged {path}")
        return
    path.write_text(content, encoding="utf-8")
    print(f"wrote {path}")


def main():
    if not TOKEN:
        print("GITHUB_TOKEN is required", file=sys.stderr)
        return 1

    today = datetime.now(timezone.utc).date()
    start = today - timedelta(days=364)
    start -= timedelta(days=(start.weekday() + 1) % 7)

    repos = fetch_repos()
    names = ", ".join(repo["name"] for repo in repos) or "(none)"
    print(f"Organization: {ORG}")
    print(f"Repositories: {names}")

    languages = Counter()
    counts = Counter()

    for repo in repos:
        name = repo["name"]
        try:
            for language, size in fetch_languages(name).items():
                languages[language] += int(size)
        except Exception as error:
            print(f"languages {name}: {error}", file=sys.stderr)
        try:
            for commit in fetch_commits(name, start):
                day = commit_date(commit)
                if day and start <= day <= today:
                    counts[day] += 1
        except Exception as error:
            print(f"commits {name}: {error}", file=sys.stderr)

    contributions = fetch_contributors([repo["name"] for repo in repos])
    avatars = {}
    for login, _ in contributions.most_common(26):
        avatars[login] = fetch_avatar(login)

    org_avatar = fetch_avatar(ORG, size=240)
    stats = {
        "repos": len(repos),
        "commits": sum(counts.values()),
        "languages": len(languages),
        "contributors": len(contributions),
    }

    for theme_name, theme in THEMES.items():
        write_if_changed(OUT / f"hero-{theme_name}.svg", hero_svg(theme, org_avatar))
        write_if_changed(OUT / f"stats-{theme_name}.svg", stats_svg(theme, stats))
        write_if_changed(
            OUT / f"commit-heatmap-{theme_name}.svg", heatmap_svg(counts, theme)
        )
        write_if_changed(
            OUT / f"languages-{theme_name}.svg", language_svg(languages, theme)
        )
        write_if_changed(
            OUT / f"contributors-{theme_name}.svg",
            contributors_svg(theme, contributions, avatars),
        )

    print(f"Stats: {stats}")
    print(f"Languages: {dict(languages)}")
    print(f"Contributors: {dict(contributions)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())