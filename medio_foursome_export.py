#!/usr/bin/env python3
"""
mga_foursomes_to_csv.py

Parse an MGA foursome list page (e.g. https://mgatour.com/events/foursome-list/17116)
into a CSV with columns: Group, Time, FirstName, LastName
"""

import argparse
import re
import sys
from datetime import datetime
from pathlib import Path

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
        resp = requests.get(source, timeout=30)
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
    """Remove leading number + dot from items like '1. Chris Dohrn'."""
    s = re.sub(r"^\s*\d+\.\s*", "", raw.strip())
    return re.sub(r"\s+", " ", s).strip()


def split_name(full: str):
    """Split into first and last name (by first space)."""
    parts = full.split(" ", 1)
    if len(parts) == 1:
        return parts[0], ""
    return parts[0], parts[1]


def parse_foursomes(html: str):
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
                first, last = split_name(player)
                out_rows.append(
                    {
                        "Group": group_num,
                        "Time": time_label,
                        "FirstName": first,
                        "LastName": last,
                    }
                )

    out_rows.sort(key=lambda r: (r["Group"], time_sort_key(r["Time"]), r["LastName"]))
    return out_rows


def write_csv(rows, output_path: str):
    import csv

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["Group", "Time", "FirstName", "LastName"])
        w.writeheader()
        w.writerows(rows)


def main():
    ap = argparse.ArgumentParser(
        description="Convert an MGA foursome list page to CSV (one player per row)."
    )
    ap.add_argument(
        "source", help="URL to the foursome list page OR a local HTML file path"
    )
    ap.add_argument(
        "-o", "--output", default="mga_foursomes.csv", help="Output CSV path"
    )
    args = ap.parse_args()

    try:
        html = load_html(args.source)
        rows = parse_foursomes(html)
        if not rows:
            sys.stderr.write("No foursome rows found.\n")
        write_csv(rows, args.output)
        print(f"Wrote {len(rows)} rows to {args.output}")
    except Exception as e:
        sys.stderr.write(f"Error: {e}\n")
        sys.exit(2)


if __name__ == "__main__":
    main()
