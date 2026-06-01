# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**qzvulner** (forked from [VulnTotal-Team/yarb](https://github.com/VulnTotal-Team/yarb)) — a Python RSS aggregation bot that collects daily security news from OPML-defined feeds, generates Markdown reports, and pushes them to multiple chat platforms. It has two runtime modes: a scheduled batch job (`yarb.py`) and an interactive WeChat Work AI bot (`wecom_ai_bot.py`) that answers natural-language queries over the report archive.

## Common Commands

```sh
# Install dependencies
./install.sh

# One-shot daily aggregation: fetch feeds, write today.md + archive
python3 yarb.py

# Refresh remote OPML files before running
python3 yarb.py --update

# Test mode with synthetic data (no real feeds, no real push unless bots enabled)
python3 yarb.py --test

# Run daily at a specific local time
python3 yarb.py --cron 11:00

# Backfill a missed archive date (e.g. cron failed on 2026-05-28)
python3 yarb.py --date 2026-05-28

# Use a custom config file
python3 yarb.py --config path/to/config.json

# Run the interactive WeChat Work AI bot (WebSocket long-running)
python3 wecom_ai_bot.py --config config.json

# Diagnose Tavily search filtering
python3 diagnose_tavily.py "产品安全漏洞" --max-results 10

# Create a deployable tar.gz package
python3 package.py --version 2026.06.01

# Run tests
python3 -m pytest tests/
```

## Architecture

### Batch pipeline (`yarb.py`)

1. `init_rss()` — loads enabled OPML sources from `config.json → rss`, optionally fetches remote OPML updates, deduplicates feed URLs by domain.
2. `parseThread()` — runs in a `ThreadPoolExecutor(100)`; one thread per feed URL. Filters articles published **yesterday** (local date) against `config.json → keywords.exclude`.
3. `update_today()` — writes results to `today.md` and `archive/<year>/<YYYY-MM-DD>.md` simultaneously.

The batch pipeline generates Markdown reports only. For push notifications, use `wecom_ai_bot.py` as a separate long-running service.

### Interactive bot (`wecom_ai_bot.py` + `report.py` + `llm.py` + `web_search.py`)

- `WeComAIBotRunner` connects via WebSocket (`wecom_aibot_sdk.WSClient`), receives `message.text` frames, and routes through `report.handle_command()`.
- Supports both **group chat** (`@机器人 命令`) and **private chat** (single chat window) — automatically detects context and routes replies accordingly.
- `handle_command()` first tries regex-based command matching (`今日安全情报`, `最近N天`, `关键词 X`, `联网搜索 X`, `刷新今日`, `帮助`, `id`, `dump`). On miss, falls back to `LLMCommandRouter` which calls an OpenAI-compatible `/chat/completions` endpoint to classify intent into a structured `LLMRoute`.
- **Progress indicators**: Long-running operations like web search send a "🔍 正在联网搜索，请稍候..." message before executing, improving user experience during multi-second LLM + Tavily operations.
- **Graceful shutdown**: Handles SIGINT (Ctrl+C) and SIGTERM signals by calling `client.disconnect()` before exiting, preventing WebSocket zombie connections that would otherwise require a 5-minute wait before reconnecting.
- `ReportStore` reads `today.md` and `archive/*/*.md`, parses them with regex, and supports today/recent/keyword queries.
- `split_message()` chunks replies at 3500 chars for WeChat Work message limits.

### Hybrid search architecture (`web_search.py` + `llm.py`)

The web search uses a hybrid approach combining LLM intelligence with parallel Tavily searches:

1. **Query expansion** — `LLMCommandRouter.expand_search_queries()` generates 3-5 complementary search queries based on domain knowledge (e.g., "TongWeb安全漏洞" → ["TongWeb EJB反序列化", "TongWeb RCE CVE", "东方通 TongWeb 安全公告"]).
2. **Parallel search** — `TavilyWebSearch._search_parallel()` executes multiple Tavily API calls concurrently using `ThreadPoolExecutor`.
3. **Deduplication** — `merge_tavily_responses()` removes duplicate URLs across all query results.
4. **Relevance reranking** — `LLMCommandRouter.rerank_results()` scores each result (0-10) based on relevance to the original query, prioritizing vendor advisories, CVE/CNVD entries, and exploit analysis.
5. **Report generation** — `LLMCommandRouter.summarize_search_results()` produces a structured Chinese report with title/source/link/summary for top results.

If LLM is unavailable or fails, the system falls back to single-query search with basic formatting.

### Push functionality

The batch pipeline (`yarb.py`) generates Markdown reports only. For push notifications, use `wecom_ai_bot.py` (WeChat Work AI bot) as a separate long-running service.

## Configuration (`config.json`)

Single source of truth. Keys:
- `proxy` — shared proxy URL, toggled per subsystem (`rss`, `web_search`).
- `rss` — each entry: `{enabled, filename, url?}`. `filename` is relative to `rss/`.
- `wecom_ai_bot` — `{bot_id_env, secret_env, allowed_chats, daily_push_time, max_reconnect_attempts}`.
- `llm` — `{api_key_env, base_url_env, model_env, timeout}` for the OpenAI-compatible router.
- `web_search` — Tavily config: `{api_key_env, max_results, search_depth, topic, include_answer, report_max_items}`.
- `keywords.exclude` — list of title substrings that cause an article to be dropped.

All secrets are read from env vars first (`os.getenv()`), falling back to config values. Never commit real keys.

## Generated Output

- **`today.md`** — overwritten on every run; the public "daily security news" page.
- **`archive/<year>/<YYYY-MM-DD>.md`** — immutable daily snapshots, also served via GitHub Pages (`_config.yml` is the Jekyll config).
- **`temp_data.json`** — intermediate results cache (currently commented out in `yarb.py`; uncomment to debug feed parsing).

## GitHub Actions

`.github/workflows/action.yml` runs daily at 02:00 UTC (10:00 Beijing). It installs deps, runs `python3 yarb.py`, then commits `today.md` + `archive/` with message `每日安全资讯（YYYY-MM-DD）`. Secrets: `FEISHU_KEY`, `WECOM_KEY`, `DINGTALK_KEY`, `QQ_KEY`, `TELEGRAM_KEY`, `MAIL_KEY`, `MAIL_RECEIVER`.

## Coding Conventions

- Python 3, 4-space indent, root-level modules (no `src/` package).
- Bot classes: `<provider>Bot` (e.g. `wecomBot`, `telegramBot`), exported via `__all__` in `bot.py`.
- Use `pathlib.Path` for repository paths; `root_path = Path(__file__).absolute().parent` is the canonical root.
- Chinese user-facing strings (console output, Markdown headings, LLM prompts) — preserve as-is.
- `from bot import *` / `from utils import *` in `yarb.py` is intentional; new modules should be added to `__all__` where applicable.

## Testing

Tests live in `tests/` and use unittest. Run with `python3 -m unittest discover tests -v`. Cover `report.py`, `llm.py`, `web_search.py`, `wecom_ai_bot.py`, and `package.py`. 

Key test scenarios:
- **Hybrid search**: Tests verify LLM-driven query expansion, parallel Tavily searches, relevance reranking, and graceful fallback when LLM fails.
- **Private chat**: Tests verify that single-chat messages (no group context) are properly detected and replied to via `send_message` instead of `reply_stream`.
- **Command routing**: Tests verify both regex-based commands and LLM fallback for natural language queries.

Before changing feed parsing, run `python3 yarb.py --test` and inspect `today.md`. For OPML changes, ensure valid XML; `init_rss` deduplicates by short domain.
