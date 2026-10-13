"""Forum Page Fetcher — plain prototype (no tool-calling).

Reads forum URLs (one per line) and fetches each page, recording HTTP status and
size to a CSV. Matches the original n8n prototype (no posting step).

    python forum_page_fetcher.py --urls forums.txt --out forums_fetched.csv
"""
from __future__ import annotations

import argparse
import csv
from datetime import datetime
from pathlib import Path

from web import fetch_page

FIELDS = ["url", "status", "bytes", "checked_at"]


def main() -> None:
    p = argparse.ArgumentParser(description="Forum page fetcher (plain prototype).")
    p.add_argument("--urls", default="forums.txt")
    p.add_argument("--out", default="forums_fetched.csv")
    a = p.parse_args()

    urls_file = Path(a.urls)
    if not urls_file.exists():
        raise SystemExit(f"URL file not found: {urls_file} (one URL per line).")
    urls = [ln.strip() for ln in urls_file.read_text(encoding="utf-8").splitlines() if ln.strip()]

    rows, ok = [], 0
    for url in urls:
        page = fetch_page(url)
        status = page.get("status")
        ok += 1 if status == 200 else 0
        rows.append({"url": url, "status": status, "bytes": page.get("bytes", 0),
                     "checked_at": datetime.now().isoformat(timespec="seconds")})
        print(f"{status}  {url}")

    with Path(a.out).open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)
    print(f"{ok}/{len(urls)} returned 200 -> {a.out}")


if __name__ == "__main__":
    main()
