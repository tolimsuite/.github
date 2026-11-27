#!/usr/bin/env python3
"""Generate the TOLIM organization profile charts: commit heatmap and languages."""

import html
import json
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

THEMES = {
    "light": {
        "text": "#24292f",
        "muted": "#57606a",
        "levels": ["#ebedf0", "#9be9a8", "#40c463", "#30a14e", "#216e39"],
    },
    "dark": {
        "text": "#c9d1d9",
        "muted": "#8b949e",
        "levels": ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"],
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
        return json.loads(response.read().decode("utf-8")), response.headers


def get_paged(path):
    url = f"{API}{path}"
    items = []
    while url:
        data, response_headers = get_json(url)
        if isinstance(data, list):
            items.extend(data)
        else:
            items.append(data)
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


def heatmap_svg(counts, theme):
    today = datetime.now(timezone.utc).date()
    start = today - timedelta(days=364)
    start -= timedelta(days=(start.weekday() + 1) % 7)
    weeks = ((today - start).days // 7) + 1

    cell, gap = 10, 3
    step = cell + gap
    grid_x, grid_y = 34, 24
    width = grid_x + weeks * step + 16
    height = grid_y + 7 * step + 26

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" '
        f'aria-label="Commit activity across TOLIM repositories over the last 12 months">',
        "<style>text{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif;}</style>",
    ]

    last_label_x = -100
    for week in range(weeks):
        for day in range(7):
            current = start + timedelta(days=week * 7 + day)
            if current.day == 1 and current <= today:
                x = grid_x + week * step + cell / 2
                if x - last_label_x >= 28:
                    parts.append(
                        f'<text x="{x:.1f}" y="12" fill="{theme["muted"]}" font-size="10" '
                        f'text-anchor="middle">{MONTHS[current.month - 1]}</text>'
                    )
                    last_label_x = x

    for row, label in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        parts.append(
            f'<text x="0" y="{grid_y + row * step + cell - 1}" fill="{theme["muted"]}" '
            f'font-size="10">{label}</text>'
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
                f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" rx="2" '
                f'fill="{fill}">{title}</rect>'
            )

    legend_y = grid_y + 7 * step + 12
    legend_x = max(grid_x, width - (5 * step + 72))
    parts.append(
        f'<text x="{legend_x - 8}" y="{legend_y + 9}" fill="{theme["muted"]}" '
        f'font-size="10" text-anchor="end">Less</text>'
    )
    for index in range(5):
        parts.append(
            f'<rect x="{legend_x + index * step}" y="{legend_y}" width="{cell}" '
            f'height="{cell}" rx="2" fill="{theme["levels"][index]}"></rect>'
        )
    parts.append(
        f'<text x="{legend_x + 5 * step + 6}" y="{legend_y + 9}" '
        f'fill="{theme["muted"]}" font-size="10">More</text>'
    )
    parts.append("</svg>")
    return "\n".join(parts)


def language_svg(lang_bytes, theme):
    items = sorted(lang_bytes.items(), key=lambda item: item[1], reverse=True)
    top = items[:6]
    other = sum(value for _, value in items[6:])
    if other:
        top.append(("Other", other))
    total = sum(value for _, value in top)

    width, height = 760, 96
    bar_x, bar_y, bar_w, bar_h = 12, 10, 736, 18
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" '
        f'aria-label="Language distribution across TOLIM repositories">',
        "<defs><clipPath id=\"bar\"><rect x=\"12\" y=\"10\" width=\"736\" height=\"18\" rx=\"5\"/></clipPath></defs>",
        "<style>text{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif;}</style>",
    ]

    if total:
        offset = 0.0
        for index, (name, value) in enumerate(top):
            share = value / total
            x = bar_x + offset * bar_w
            width_value = bar_x + bar_w - x if index == len(top) - 1 else share * bar_w
            color = LANG_COLORS.get(name, FALLBACK_COLORS[index % len(FALLBACK_COLORS)])
            percentage = share * 100
            parts.append(
                f'<rect x="{x:.2f}" y="{bar_y}" width="{max(width_value, 0):.2f}" '
                f'height="{bar_h}" fill="{color}" clip-path="url(#bar)">'
                f"<title>{html.escape(name)}: {percentage:.1f}%</title></rect>"
            )
            offset += share
    else:
        parts.append(
            f'<text x="{bar_x}" y="{bar_y + 14}" fill="{theme["muted"]}" font-size="12">'
            "No language data yet</text>"
        )

    if total:
        column_width = bar_w / 4
        for index, (name, value) in enumerate(top):
            column = index % 4
            row = index // 4
            x = bar_x + column * column_width
            y = bar_y + bar_h + 22 + row * 18
            color = LANG_COLORS.get(name, FALLBACK_COLORS[index % len(FALLBACK_COLORS)])
            percentage = value / total * 100
            parts.append(
                f'<rect x="{x}" y="{y - 7}" width="8" height="8" rx="2" fill="{color}"></rect>'
            )
            parts.append(
                f'<text x="{x + 13}" y="{y}" fill="{theme["text"]}" font-size="11">'
                f'{html.escape(name)} <tspan fill="{theme["muted"]}">{percentage:.1f}%</tspan></text>'
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

    for theme_name, theme in THEMES.items():
        write_if_changed(
            OUT / f"commit-heatmap-{theme_name}.svg", heatmap_svg(counts, theme)
        )
        write_if_changed(
            OUT / f"languages-{theme_name}.svg", language_svg(languages, theme)
        )

    print(f"Languages: {dict(languages)}")
    print(f"Commits in the last 12 months: {sum(counts.values())}")
    return 0


if __name__ == "__main__":
    sys.exit(main())