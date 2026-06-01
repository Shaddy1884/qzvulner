#!/usr/bin/python3

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Any


ARTICLE_RE = re.compile(r"^\s{2}- \[(?P<title>.+?)\]\((?P<url>.+?)\)\s*$")
SOURCE_RE = re.compile(r"^- (?P<source>.+?)\s*$")
DATE_RE = re.compile(r"每日安全资讯（(?P<date>\d{4}-\d{2}-\d{2})）")


@dataclass(frozen=True)
class Article:
    day: str
    source: str
    title: str
    url: str


def parse_report_markdown(text: str, fallback_day: str = "") -> list[Article]:
    match = DATE_RE.search(text)
    day = match.group("date") if match else fallback_day
    source = ""
    articles: list[Article] = []

    for line in text.splitlines():
        if source_match := SOURCE_RE.match(line):
            source = source_match.group("source")
            continue
        if article_match := ARTICLE_RE.match(line):
            articles.append(Article(
                day=day,
                source=source,
                title=article_match.group("title"),
                url=article_match.group("url"),
            ))
    return articles


class ReportStore:
    def __init__(self, root: Path | str = ".", today: date | None = None, config: str | None = None) -> None:
        self.root = Path(root)
        self.today = today or date.today()
        self.config = config

    def today_report(self) -> str:
        path = self.root / "today.md"
        if not path.exists():
            return self._empty_today()
        text = path.read_text(encoding="utf-8")
        if not parse_report_markdown(text, self.today.isoformat()):
            return self._empty_today()
        return text.strip()

    def recent_report(self, days: int) -> str:
        sections: list[str] = [f"最近{days}天安全情报"]
        missing: list[str] = []

        for offset in range(days):
            current = self.today - timedelta(days=offset)
            day = current.isoformat()
            path = self.root / "archive" / str(current.year) / f"{day}.md"
            if not path.exists():
                missing.append(day)
                continue
            articles = parse_report_markdown(path.read_text(encoding="utf-8"), day)
            if articles:
                sections.append(self._format_day(day, articles))
            else:
                sections.append(f"\n## {day}\n今日暂无安全情报。")

        if missing:
            sections.append("\n缺失归档：" + "、".join(missing))
        if len(sections) == 1:
            sections.append("\n暂无可用归档。")
        return "\n\n".join(sections).strip()

    def keyword_report(self, keyword: str, limit: int = 20) -> str:
        keyword = keyword.strip()
        if not keyword:
            return "请提供关键词，例如：关键词 RCE"

        matches = [
            article for article in self._all_articles()
            if _keyword_matches(article.title, keyword)
        ]
        matches.sort(key=lambda item: item.day, reverse=True)
        matches = matches[:limit]

        if not matches:
            return f"关键词：{keyword}\n\n未找到匹配的归档标题。"

        lines = [f"关键词：{keyword}", ""]
        current_day = ""
        for article in matches:
            if article.day != current_day:
                current_day = article.day
                lines.append(current_day)
            lines.append(f"- [{article.source}] {article.title}")
            lines.append(f"  {article.url}")
        lines.append("")
        lines.append(f"共找到 {len(matches)} 条，已显示最近 {len(matches)} 条。")
        return "\n".join(lines).strip()

    def refresh_today(self, config: str | None = None) -> str:
        config = config or self.config
        cmd = [sys.executable, str(self.root / "yarb.py")]
        if config:
            cmd.extend(["--config", config])
        result = subprocess.run(cmd, cwd=self.root, text=True, capture_output=True)
        if result.returncode != 0:
            return "刷新今日失败：\n" + (result.stderr or result.stdout).strip()
        return self.today_report()

    def _all_articles(self) -> list[Article]:
        seen: set[tuple[str, str, str, str]] = set()
        articles: list[Article] = []

        for path in sorted((self.root / "archive").glob("*/*.md")):
            items = parse_report_markdown(path.read_text(encoding="utf-8"), path.stem)
            for item in items:
                key = (item.day, item.source, item.title, item.url)
                if key not in seen:
                    seen.add(key)
                    articles.append(item)

        today_path = self.root / "today.md"
        if today_path.exists():
            for item in parse_report_markdown(today_path.read_text(encoding="utf-8"), self.today.isoformat()):
                key = (item.day, item.source, item.title, item.url)
                if key not in seen:
                    seen.add(key)
                    articles.append(item)

        return articles

    def _empty_today(self) -> str:
        return f"每日安全情报（{self.today.isoformat()}）\n\n今日暂无安全情报。"

    @staticmethod
    def _format_day(day: str, articles: list[Article]) -> str:
        lines = [f"\n## {day}"]
        current_source = ""
        for article in articles:
            if article.source != current_source:
                current_source = article.source
                lines.append(f"- {current_source}")
            lines.append(f"  - [{article.title}]({article.url})")
        return "\n".join(lines)


def help_text() -> str:
    return """可用命令：
帮助
id
今日安全情报
最近3天
关键词 RCE
联网搜索 CVE-2026
刷新今日"""


def _keyword_matches(value: str, keyword: str) -> bool:
    if re.fullmatch(r"[A-Za-z0-9]+", keyword):
        pattern = rf"(?<![A-Za-z0-9]){re.escape(keyword)}(?![A-Za-z0-9])"
        return bool(re.search(pattern, value, re.IGNORECASE))
    return keyword.lower() in value.lower()


def handle_command(
    text: str,
    store: ReportStore,
    conversation_id: str = "",
    refresh_callback=None,
    llm_router: Any = None,
    web_search: Any = None,
) -> str:
    command = text.strip()
    if command.startswith("@"):
        command = command.split(maxsplit=1)[1] if " " in command else ""

    if llm_router and _is_natural_web_search(command):
        try:
            route = llm_router.route(command)
        except Exception as exc:
            return "LLM 解析失败，已回退到帮助。\n\n" + str(exc) + "\n\n" + help_text()
        response = execute_route(route.action, route.value, store, conversation_id, refresh_callback, web_search)
        if response:
            return response

    response = execute_command(command, store, conversation_id, refresh_callback, web_search)
    if response:
        return response

    if llm_router and command:
        try:
            route = llm_router.route(command)
        except Exception as exc:
            return "LLM 解析失败，已回退到帮助。\n\n" + str(exc) + "\n\n" + help_text()
        response = execute_route(route.action, route.value, store, conversation_id, refresh_callback, web_search)
        if response:
            return response

    return help_text()


def execute_command(
    command: str,
    store: ReportStore,
    conversation_id: str = "",
    refresh_callback=None,
    web_search: Any = None,
) -> str:
    if command in {"帮助", "help", "/help"}:
        return help_text()
    if command.lower() == "id":
        return f"当前会话 ID：{conversation_id or 'unknown'}"
    if command in {"今日安全情报", "今日", "today"}:
        return store.today_report()
    if match := re.fullmatch(r"最近(\d+)天", command):
        return store.recent_report(int(match.group(1)))
    if command.startswith("关键词 "):
        return store.keyword_report(command.split(maxsplit=1)[1])
    if command.startswith("联网搜索 "):
        return execute_route("web_search", command.split(maxsplit=1)[1], store, conversation_id, refresh_callback, web_search)
    if match := re.fullmatch(r"(?:搜索|查找|查询)\s*(.+)", command):
        return execute_route("web_search", match.group(1), store, conversation_id, refresh_callback, web_search)
    if command == "刷新今日":
        if refresh_callback:
            return refresh_callback()
        return store.refresh_today()
    return ""


def _is_natural_web_search(command: str) -> bool:
    return bool(re.fullmatch(r"(?:搜索|查找|查询)\s*.+", command.strip()))


def execute_route(
    action: str,
    value: str,
    store: ReportStore,
    conversation_id: str = "",
    refresh_callback=None,
    web_search: Any = None,
) -> str:
    action = action.strip().lower()
    value = value.strip()
    if action == "help":
        return help_text()
    if action == "id":
        return f"当前会话 ID：{conversation_id or 'unknown'}"
    if action == "today":
        return store.today_report()
    if action == "recent":
        days = int(value) if value.isdigit() else 3
        return store.recent_report(max(1, min(days, 30)))
    if action == "keyword":
        return store.keyword_report(value)
    if action == "web_search":
        if not web_search:
            return "联网搜索未启用，请在 config.json 配置 web_search 并设置 TAVILY_API_KEY。"
        try:
            return web_search.search_report(value)
        except Exception as exc:
            return f"Tavily 联网搜索失败：{exc}\n\n请检查运行环境 DNS、出口网络或代理配置。"
    if action == "refresh":
        if refresh_callback:
            return refresh_callback()
        return store.refresh_today()
    return ""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["today", "recent", "keyword", "refresh"])
    parser.add_argument("value", nargs="?")
    parser.add_argument("--root", default=".")
    parser.add_argument("--config", default=None)
    parser.add_argument("--days", type=int, default=3)
    args = parser.parse_args()

    store = ReportStore(args.root, config=args.config)
    if args.command == "today":
        print(store.today_report())
    elif args.command == "recent":
        print(store.recent_report(args.days))
    elif args.command == "keyword":
        print(store.keyword_report(args.value or ""))
    elif args.command == "refresh":
        print(store.refresh_today())


if __name__ == "__main__":
    main()
