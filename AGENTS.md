# Repository Guidelines

## Project Structure & Module Organization

This repository is a Python RSS aggregation and notification bot. Core runtime code lives at the repository root: `yarb.py` orchestrates feed loading, parsing, scheduling, archive generation, and bot dispatch; `bot.py` contains notification adapters; `utils.py` contains shared helpers. Feed definitions are stored in `rss/*.opml`. Generated public content is written to `today.md` and date-based archives under `archive/<year>/<YYYY-MM-DD>.md`. GitHub Actions automation lives in `.github/workflows/action.yml`; Jekyll Pages configuration is in `_config.yml`.

## Build, Test, and Development Commands

- `python3 -m pip install -r requirements.txt`: install Python dependencies.
- `./install.sh`: install Python dependencies from `requirements.txt`.
- `python3 yarb.py --help`: list supported runtime flags.
- `python3 yarb.py`: run one daily aggregation job using `config.json`.
- `python3 yarb.py --update`: refresh remote OPML feed files before running.
- `python3 yarb.py --cron 11:00`: run the job daily at the specified local time.
- `python3 yarb.py --test`: run with synthetic test data; keep bots disabled unless you intend to send messages.

## Coding Style & Naming Conventions

Use Python 3 and keep the existing lightweight style: 4-space indentation, root-level modules, simple functions, and bot classes named `<provider>Bot` such as `wecomBot` and `telegramBot`. Prefer `pathlib.Path` for repository paths and keep JSON keys aligned with `config.json`. Preserve Chinese user-facing messages and Markdown headings where they already exist.

## Testing Guidelines

There is no formal test suite. Before submitting code changes, run `python3 yarb.py --test` and, for feed-related changes, run with a temporary config that disables all bots. Verify `today.md` and `archive/<year>/` changes are expected. For OPML changes, ensure files remain valid XML and feed URLs are deduplicated by `init_rss`.

## Commit & Pull Request Guidelines

Recent history uses Chinese daily-update commits such as `每日安全资讯（2026-05-27）`. For non-automated changes, use a concise imperative summary, preferably scoped, for example `修复 Telegram 推送代理配置`. Pull requests should describe behavior changes, list manual test commands, note config or secret requirements, and include sample output or screenshots when Markdown rendering changes.

## Security & Configuration Tips

Do not commit real bot keys, mail authorization codes, chat IDs, or proxy credentials. Use environment variables named in `config.json` and GitHub Actions secrets (`FEISHU_KEY`, `WECOM_KEY`, `DINGTALK_KEY`, `QQ_KEY`, `TELEGRAM_KEY`, `MAIL_KEY`, `MAIL_RECEIVER`). When using Codex in this repo, prefix shell commands with `rtk` per local agent instructions.
