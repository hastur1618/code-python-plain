"""Topic Queue to Docs — plain pipeline (no tool-calling).

Reads a queue of topics (one per line), writes a long-form article for each, and
saves each as a Markdown document.

Env: OPENAI_API_KEY, OPENAI_MODEL (optional).

    python topic_queue_to_docs.py --topics topics.txt --brand "AcmeTravel" --out docs
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

from common import get_client, get_model

SYSTEM = ("You are a content writer. Write normal paragraphs (no Markdown symbols "
          "in the body). Mention the brand once, in the first paragraph only.")


def write_article(client, model, topic, brand) -> str:
    user = (f'Write a long-form article (at least 2,500-3,000 characters) on: "{topic}". '
            f'Mention the brand "{brand}" once, in the first paragraph. Return only the text.')
    r = client.chat.completions.create(
        model=model,
        messages=[{"role": "system", "content": SYSTEM},
                  {"role": "user", "content": user}],
    )
    return (r.choices[0].message.content or "").strip()


def main() -> None:
    p = argparse.ArgumentParser(description="Topic queue to docs (plain).")
    p.add_argument("--topics", default="topics.txt")
    p.add_argument("--brand", default="{{CLIENT_BRAND}}")
    p.add_argument("--out", default="docs")
    a = p.parse_args()

    topics_file = Path(a.topics)
    if not topics_file.exists():
        raise SystemExit(f"Topics file not found: {topics_file} (one topic per line).")
    topics = [ln.strip() for ln in topics_file.read_text(encoding="utf-8").splitlines() if ln.strip()]
    if not topics:
        raise SystemExit("The topic queue is empty.")

    client, model = get_client(), get_model()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    for i, topic in enumerate(topics, 1):
        print(f"[{i}/{len(topics)}] {topic}")
        try:
            text = write_article(client, model, topic, a.brand)
        except Exception as exc:
            print(f"    skipped ({exc})")
            continue
        safe = re.sub(r'[\\/:*?"<>|]', "", topic).strip()[:80] or "document"
        path = out / f"{safe}.md"
        path.write_text(f"# {topic}\n\n{text}\n", encoding="utf-8")
        print(f"    saved {path}")
    print("Done.")


if __name__ == "__main__":
    main()
