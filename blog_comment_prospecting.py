"""Blog Comment Prospecting — plain pipeline (no tool-calling, no LLM).

For each niche it builds search footprints, searches via Serper, de-duplicates
by domain, fetches each page, applies CMS / comment-form heuristics, and writes
sites that have a comment form to a CSV with a status.

Env: SERPER_API_KEY.

    python blog_comment_prospecting.py --niches "casino,sport betting" --out prospects.csv
"""
from __future__ import annotations

import argparse
import csv
from datetime import datetime
from pathlib import Path

from web import analyze_html, domain_of, fetch_page, serper_search

FOOTPRINTS = [
    '"powered by wordpress" "leave a comment" {niche} blog',
    '"{niche}" "post a comment" inurl:blog',
    '"{niche}" "add a comment" -inurl:login',
]
FIELDS = ["url", "cms", "has_comment_form", "requires_registration",
          "niche", "status", "checked_at"]


def run(niches: list[str], out_path: Path) -> None:
    seen: set[str] = set()
    rows: list[dict] = []
    for niche in niches:
        for fp in FOOTPRINTS:
            query = fp.format(niche=niche)
            print(f"[search] {query}")
            for item in serper_search(query, num=10):
                url = item.get("link")
                if not url:
                    continue
                dom = domain_of(url)
                if dom in seen:
                    continue
                seen.add(dom)
                page = fetch_page(url)
                if page.get("status") != 200 or not page.get("html"):
                    continue
                v = analyze_html(page["html"])
                if not v["has_comment_form"]:
                    continue
                status = ("ready_to_contact"
                          if not v["requires_registration"] else "needs_review")
                rows.append({"url": url, "cms": v["cms"],
                             "has_comment_form": v["has_comment_form"],
                             "requires_registration": v["requires_registration"],
                             "niche": niche, "status": status,
                             "checked_at": datetime.now().isoformat(timespec="seconds")})
                print(f"    + {dom} [{status}]")

    with out_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)
    ready = sum(1 for r in rows if r["status"] == "ready_to_contact")
    print(f"Saved {len(rows)} prospects ({ready} ready_to_contact) -> {out_path}")


def main() -> None:
    p = argparse.ArgumentParser(description="Blog comment prospecting (plain).")
    p.add_argument("--niches", default="casino,sport betting")
    p.add_argument("--out", default="prospects.csv")
    a = p.parse_args()
    run([n.strip() for n in a.niches.split(",") if n.strip()], Path(a.out))


if __name__ == "__main__":
    main()
