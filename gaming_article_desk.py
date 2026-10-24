"""
Gaming Article Desk — Python version of the n8n workflow.

Pipeline:
  1. Research fresh gaming topics with the OpenAI Responses API (web search tool).
  2. For each topic, write a style-controlled article with one in-context link.
  3. Save every article as a .txt file.

The OpenAI API key is read from the OPENAI_API_KEY environment variable.
No keys are hard-coded.

Usage:
    export OPENAI_API_KEY="sk-..."
    pip install -r requirements.txt     # openai>=1.40
    python gaming_article_desk.py --topics 3 --language english \
        --anchor "best project management tools" --url "https://example.com"

Run `python gaming_article_desk.py --help` for all options.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #
@dataclass
class Config:
    topics_count: int
    language: str
    anchor_text: str
    target_url: str
    model: str
    out_dir: Path


def parse_args(argv: list[str] | None = None) -> Config:
    p = argparse.ArgumentParser(description="Generate gaming articles with OpenAI.")
    p.add_argument("--topics", type=int, default=3, help="How many topics/articles to produce.")
    p.add_argument("--language", default="english", help='Article language, e.g. "english" or "français".')
    p.add_argument("--anchor", default="1111", help="Anchor text for the single in-context link.")
    p.add_argument("--url", default="https://example.com", help="Target URL the anchor links to.")
    p.add_argument("--model", default="gpt-4o", help="OpenAI model for article writing.")
    p.add_argument("--out", default="articles", help="Output directory for .txt files.")
    a = p.parse_args(argv)
    return Config(
        topics_count=max(1, a.topics),
        language=a.language.strip(),
        anchor_text=a.anchor.strip(),
        target_url=a.url.strip(),
        model=a.model.strip(),
        out_dir=Path(a.out),
    )


# --------------------------------------------------------------------------- #
# OpenAI client
# --------------------------------------------------------------------------- #
def make_client():
    """Create an OpenAI client or exit with a clear message."""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        sys.exit("ERROR: set the OPENAI_API_KEY environment variable before running.")
    try:
        from openai import OpenAI
    except ImportError:
        sys.exit("ERROR: the 'openai' package is missing. Run: pip install openai>=1.40")
    return OpenAI(api_key=api_key)


def _strip_code_fences(text: str) -> str:
    """Remove ```json ... ``` fences the model sometimes adds."""
    return re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.MULTILINE).strip()


# --------------------------------------------------------------------------- #
# Step 1 — research topics (Responses API + web search)
# --------------------------------------------------------------------------- #
def research_topics(client, cfg: Config) -> list[str]:
    prompt = (
        f"Find {cfg.topics_count} concrete, specific article topics about the gaming "
        f"industry, based on recent news (patches, releases, events, tournaments). "
        f"Topics must be in {cfg.language}. Avoid generic or promotional titles. "
        f'Return ONLY a JSON array of strings, e.g. ["Topic one", "Topic two"].'
    )
    resp = client.responses.create(
        model=cfg.model,
        tools=[{"type": "web_search_preview"}],
        input=prompt,
    )
    raw = _strip_code_fences(resp.output_text or "")
    try:
        topics = json.loads(raw)
        if not isinstance(topics, list) or not topics:
            raise ValueError
    except (json.JSONDecodeError, ValueError):
        sys.exit(f"ERROR: could not parse topics as JSON. Model returned:\n{raw[:500]}")
    return [str(t).strip() for t in topics][: cfg.topics_count]


# --------------------------------------------------------------------------- #
# Step 2 — write one article
# --------------------------------------------------------------------------- #
def write_article(client, cfg: Config, topic: str) -> str:
    system = (
        "You are an experienced gaming journalist. Write engaging, human-sounding "
        "articles that read as useful content for people, not as SEO text."
    )
    user = (
        f'Write an article in {cfg.language} on the topic: "{topic}".\n'
        f"Requirements:\n"
        f"- 2,500-3,500 characters.\n"
        f"- Varied sentence rhythm, a first-person opinion, concrete details.\n"
        f"- No clichés or canned transitions. At most one bullet list.\n"
        f'- Include exactly one link: anchor text "{cfg.anchor_text}" pointing to '
        f"{cfg.target_url}, placed naturally in context as your recommendation "
        f"(not in the first or last paragraph).\n"
        f"- Return only the article text."
    )
    resp = client.chat.completions.create(
        model=cfg.model,
        max_tokens=1200,
        messages=[{"role": "system", "content": system},
                  {"role": "user", "content": user}],
    )
    return (resp.choices[0].message.content or "").strip()


# --------------------------------------------------------------------------- #
# Step 3 — save
# --------------------------------------------------------------------------- #
def save_article(text: str, topic: str, cfg: Config) -> Path:
    cfg.out_dir.mkdir(parents=True, exist_ok=True)
    safe = re.sub(r'[\\/:*?"<>|]', "", topic).strip()[:80] or "article"
    stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    path = cfg.out_dir / f"{safe} [{cfg.language}] {stamp}.txt"
    path.write_text(text, encoding="utf-8")
    return path


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def main() -> None:
    cfg = parse_args()
    client = make_client()

    print(f"Researching {cfg.topics_count} topic(s) in {cfg.language} ...")
    topics = research_topics(client, cfg)

    for i, topic in enumerate(topics, 1):
        print(f"[{i}/{len(topics)}] writing: {topic}")
        try:
            article = write_article(client, cfg, topic)
        except Exception as exc:  # keep going on a single failure
            print(f"    skipped (error: {exc})")
            continue
        path = save_article(article, topic, cfg)
        print(f"    saved: {path}  ({len(article)} chars)")

    print("Done.")


if __name__ == "__main__":
    main()
