#!/usr/bin/env python3
"""
medio_foursome_export.py

Parse foursomes from an MGA tournament page
into a CSV with columns: Time, Group, FirstName, LastName, Nickname
"""

import argparse
import re
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    sys.stderr.write(
        "Missing dependencies. Install with:\n"
        "  pip install requests beautifulsoup4\n"
    )
    sys.exit(1)


def load_html(source: str) -> str:
    """Load HTML from a URL or local file path."""
    if re.match(r"^https?://", source, re.I):
        parsed = urlparse(source)
        q = dict(parse_qsl(parsed.query, keep_blank_values=True))
        q["_cb"] = str(int(datetime.now().timestamp()))
        url = urlunparse(parsed._replace(query=urlencode(q)))
        headers = {
            "User-Agent": "Python",
            "Cache-Control": "no-cache, no-store, max-age=0",
            "Pragma": "no-cache",
            "Expires": "0",
        }
        resp = requests.get(url, headers=headers, timeout=30)
        resp.raise_for_status()
        return resp.text
    p = Path(source)
    if not p.exists():
        raise FileNotFoundError(f"No such file: {source}")
    return p.read_text(encoding="utf-8", errors="ignore")


def parse_time_label(t: str) -> str:
    """Normalize time label, keep AM/PM (e.g., '9:06AM')."""
    t = t.strip().upper().replace(" ", "")
    t = re.sub(r"[^0-9:APM]", "", t)
    dt = datetime.strptime(t, "%I:%M%p")
    # Format with AM/PM preserved
    return dt.strftime("%-I:%M%p") if sys.platform != "win32" else dt.strftime("%I:%M%p").lstrip("0")


def time_sort_key(t: str):
    """Turn '9:06AM' into a sortable (hour, minute, am/pm)."""
    dt = datetime.strptime(t.upper().replace(" ", ""), "%I:%M%p")
    return (dt.hour, dt.minute)


def group_number(group_label: str) -> int:
    """Extract numeric group from 'Group 7' -> 7."""
    m = re.search(r"(\d+)", group_label)
    return int(m.group(1)) if m else 0


def clean_player(raw: str) -> str:
    """Remove leading number + dot from items."""
    s = re.sub(r"^\s*\d+\.\s*", "", raw.strip())
    return re.sub(r"\s+", " ", s).strip()


def split_name(full: str):
    """Split into first/last name and extract quoted nickname (if present)."""
    nickname = ""
    m = re.search(r'"[^"]+"', full)
    if m:
        nickname = m.group(0)  # Preserve surrounding quotes
        full = (full[:m.start()] + " " + full[m.end():]).strip()
        full = re.sub(r"\s+", " ", full)

    parts = full.split(" ", 1)
    if len(parts) == 1:
        return parts[0], "", nickname
    return parts[0], parts[1], nickname


def maybe_prompt_guest_name(player: str, prompt_guests: bool) -> str:
    """Optionally replace guest placeholder text with an entered name."""
    if not prompt_guests:
        return player

    if not re.fullmatch(r"Guest \d+ \.", player, re.I):
        return player

    num_match = re.search(r"\d+", player)
    if not num_match:
        return player

    guest_num = num_match.group(0)
    entered = input(f"Enter full name for Guest #{guest_num}: ").strip()
    return entered if entered else player


def parse_foursomes(html: str, prompt_guests: bool = False):
    """Return a list of dicts: {Group, Time, FirstName, LastName}"""
    soup = BeautifulSoup(html, "html.parser")
    out_rows = []

    for fs in soup.select("div.foursomes div.foursome"):
        header = fs.select_one(".list-header")
        if not header:
            continue

        header_text = header.get_text(" ", strip=True)
        parts = [p.strip() for p in header_text.split("-")]
        group_label = parts[0] if parts else "Group 0"
        time_label = parts[1] if len(parts) > 1 else ""

        group_num = group_number(group_label)
        if time_label:
            time_label = parse_time_label(time_label)

        for li in fs.select("ul li"):
            txt = li.get_text(" ", strip=True)
            player = clean_player(txt)
            if player:
                player = maybe_prompt_guest_name(player, prompt_guests)
                first, last, nickname = split_name(player)
                out_rows.append(
                    {
                        "Group": group_num,
                        "Time": time_label,
                        "FirstName": first,
                        "LastName": last,
                        "Nickname": nickname,
                    }
                )

    out_rows.sort(key=lambda r: (r["Group"], time_sort_key(r["Time"]), r["LastName"]))
    return out_rows


def write_csv(rows, output_path: str):
    import csv

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(
            f, fieldnames=["Time", "Group", "FirstName", "LastName", "Nickname"]
        )
        w.writeheader()
        w.writerows(rows)


def default_output_path(source: str) -> Path:
    """Build a default CSV path in ~/Documents from the source slug/stem."""
    slug = ""
    if re.match(r"^https?://", source, re.I):
        parsed = urlparse(source)
        slug = Path(parsed.path).name
    else:
        slug = Path(source).stem

    slug = re.sub(r"[^a-zA-Z0-9-]+", "-", slug).strip("-").lower()
    if not slug:
        slug = "mga-foursomes"

    return Path.home() / "Documents" / f"foursomes-{slug}.csv"


def main():
    ap = argparse.ArgumentParser(
        description="Convert an MGA foursome list page to CSV (one player per row)."
    )
    ap.add_argument(
        "source", help="URL to the foursome list page OR a local HTML file path"
    )
    ap.add_argument("-o", "--output", help="Output CSV path")
    ap.add_argument(
        "--prompt-guests",
        action="store_true",
        help="Prompt for guest names when placeholders like 'Guest #12 .' are encountered",
    )
    args = ap.parse_args()

    try:
        html = load_html(args.source)
        rows = parse_foursomes(html, prompt_guests=args.prompt_guests)
        if not rows:
            sys.stderr.write("No foursome rows found.\n")
        output_path = Path(args.output) if args.output else default_output_path(args.source)
        write_csv(rows, str(output_path))
        print(f"Wrote {len(rows)} rows to {output_path}")
    except Exception as e:
        sys.stderr.write(f"Error: {e}\n")
        sys.exit(2)


if __name__ == "__main__":
    main()
