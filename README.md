# n8n workflows as plain Python (no tool-calling)

Straight-line Python versions of my n8n workflows — direct scripts, **no agent
loop and no tool-calling**. Each workflow is a separate file; the LLM (where used)
is called directly.

[Описание на русском](#на-русском)

## Scripts

| Script | What it does | Uses the LLM? | External service |
| --- | --- | --- | --- |
| `gaming_article_desk.py` | Research topics (web search), write and save articles | yes | OpenAI, Serper* |
| `blog_comment_prospecting.py` | Search, de-dupe, fetch, classify, save prospects to CSV | no (heuristics) | Serper |
| `bulk_article_generator.py` | Generate a batch of placement articles | yes | OpenAI |
| `topic_queue_to_docs.py` | Topic queue → long article → Markdown doc | yes | OpenAI |
| `forum_page_fetcher.py` | Prototype: fetch forum pages, record status | no | — |
| `telegram_content_bot.py` | Interactive Telegram bot with LLM generation | yes | OpenAI, Telegram |

\* `gaming_article_desk.py` uses the OpenAI Responses API web-search tool for topic
research; `SERPER_API_KEY` is not required for that one.

Shared helpers: `common.py` (OpenAI client/model from env) and `web.py`
(page fetch, Serper search, CMS/comment heuristics).

## Setup and run

```bash
pip install -r requirements.txt
cp .env.example .env            # fill in keys
export $(grep -v '^#' .env | xargs)

python gaming_article_desk.py --topics 3 --language english --anchor "best crypto casinos" --url "https://example.com"
python blog_comment_prospecting.py --niches "casino,sport betting"
python bulk_article_generator.py --count 5 --brand "AcmeBet"
python topic_queue_to_docs.py --topics topics.txt --brand "AcmeBet"
python forum_page_fetcher.py --urls forums.txt
python telegram_content_bot.py
```

Keys are read from the environment; nothing is hard-coded. Output is saved locally
(`.txt`, `.md`, `.csv`).

## На русском

Прямые Python-версии воркфлоу — **без агентного цикла и без tool-calling**. Каждый
воркфлоу отдельным файлом, модель (где нужна) вызывается напрямую. Часть скриптов
(`blog_comment_prospecting`, `forum_page_fetcher`) вообще не используют LLM — только
поиск, загрузку страниц и эвристики. Ключи — из окружения, результаты сохраняются
локально.
