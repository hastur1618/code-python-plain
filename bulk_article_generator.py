"""Bulk Article Generator — plain pipeline (no tool-calling).

Generates a batch of plain-text articles with one brand mention each and saves
every article to its own file.

Env: OPENAI_API_KEY, OPENAI_MODEL (optional).

    python bulk_article_generator.py --count 5 --brand "AcmeBet" --niche "online casino"
"""
from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

from common import get_client, get_model

SYSTEM = ("You are a content writer. Write plain text only (no Markdown, hashtags "
          "or bullet symbols). Mention the given brand exactly once.")


def write_article(client, model, niche, brand) -> str:
    user = (f"Write an 800-1500 word article in the {niche} niche on a popular, "
            f"specific sub-topic (bonuses, slots, live dealer, crypto payments, "
            f"mobile apps, etc.). Intro, 2-3 sections, conclusion. No keyword "
            f'stuffing. Mention the brand "{brand}" exactly once. Return only the text.')
    r = client.chat.completions.create(
        model=model,
        messages=[{"role": "system", "content": SYSTEM},
                  {"role": "user", "content": user}],
    )
    return (r.choices[0].message.content or "").strip()


def main() -> None:
    p = argparse.ArgumentParser(description="Bulk article generator (plain).")
    p.add_argument("--count", type=int, default=5)
    p.add_argument("--brand", default="{{CLIENT_BRAND}}")
    p.add_argument("--niche", default="online casino")
    p.add_argument("--out", default="articles")
    a = p.parse_args()

    client, model = get_client(), get_model()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    for i in range(1, max(1, a.count) + 1):
        print(f"[{i}/{a.count}] writing ...")
        try:
            text = write_article(client, model, a.niche, a.brand)
        except Exception as exc:
            print(f"    skipped ({exc})")
            continue
        stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        path = out / f"article_{i:03d}_{stamp}.txt"
        path.write_text(text, encoding="utf-8")
        print(f"    saved {path} ({len(text)} chars)")
    print("Done.")


if __name__ == "__main__":
    main()
