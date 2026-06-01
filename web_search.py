#!/usr/bin/python3

import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

import requests


DEFAULT_MAX_RESULTS = 5
MAX_PARALLEL_SEARCHES = 5

# 搜索结果中排除的低质量站点（内容农场、SEO 聚合、搬运站）
EXCLUDE_DOMAINS = [
    "csdn.net",
    "cnblogs.com",
    "scribd.com",
]


@dataclass
class TavilyWebSearch:
    api_key: str
    max_results: int = DEFAULT_MAX_RESULTS
    search_depth: str = "basic"
    topic: str = "general"
    include_answer: bool = True
    report_max_items: int = 6
    proxy_url: str = ""
    result_summarizer: Any = None
    _client: Any = None

    @classmethod
    def from_config(cls, config: dict[str, Any]) -> "TavilyWebSearch | None":
        search_conf = config.get("web_search", {})
        if not search_conf.get("enabled", False):
            return None

        api_key_env = search_conf.get("api_key_env", "TAVILY_API_KEY")
        api_key = os.getenv(api_key_env) or search_conf.get("api_key", "")
        if not api_key:
            raise RuntimeError(f"Tavily 联网搜索已启用，请设置环境变量 {api_key_env}")

        proxy_conf = config.get("proxy", {})
        proxy_url = proxy_conf.get("url", "") if proxy_conf.get("web_search", False) else ""

        return cls(
            api_key=api_key,
            max_results=int(search_conf.get("max_results", DEFAULT_MAX_RESULTS)),
            search_depth=search_conf.get("search_depth", "basic"),
            topic=search_conf.get("topic", "general"),
            include_answer=bool(search_conf.get("include_answer", True)),
            report_max_items=int(search_conf.get("report_max_items", 6)),
            proxy_url=proxy_url,
        )

    def search_report(self, query: str) -> str:
        query = query.strip()
        if not query:
            return "请提供联网搜索关键词，例如：联网搜索 CVE-2026"

        try:
            # Step 1: Generate search queries (LLM or fallback)
            search_queries = self._build_queries(query)

            # Step 2: Parallel search
            response = self._search_parallel(search_queries)

            # Step 3: LLM reranking (if available)
            if self.result_summarizer and response.get("results"):
                try:
                    reranked = self.result_summarizer.rerank_results(
                        query,
                        response["results"],
                        top_k=self.report_max_items,
                    )
                    response["results"] = reranked
                except Exception as exc:
                    # Fallback to original results if reranking fails
                    pass

            # Step 4: Generate report (LLM or fallback)
            if self.result_summarizer:
                try:
                    llm_report = self.result_summarizer.summarize_search_results(
                        query,
                        response,
                        max_items=self.report_max_items,
                    )
                    return llm_report
                except Exception as exc:
                    return format_tavily_response(query, response, self.report_max_items) + f"\n\nLLM 整理失败：{exc}"

            return format_tavily_response(query, response, self.report_max_items)

        except requests.RequestException as exc:
            return f"Tavily 联网搜索失败：{exc}\n\n请检查运行环境 DNS、出口网络或代理配置。"

    def _build_queries(self, query: str) -> list[str]:
        """Generate search queries using LLM (if available) or hardcoded fallback."""
        if self.result_summarizer:
            try:
                queries = self.result_summarizer.expand_search_queries(
                    query,
                    max_queries=MAX_PARALLEL_SEARCHES,
                )
                if queries:
                    return queries
            except Exception:
                pass
        # Fallback to hardcoded expansion
        return build_search_queries(query)

    def _search_parallel(self, queries: list[str]) -> dict[str, Any]:
        """Execute multiple Tavily searches in parallel."""
        per_query_limit = max(3, self.max_results // 2)
        responses = []

        with ThreadPoolExecutor(max_workers=min(len(queries), MAX_PARALLEL_SEARCHES)) as executor:
            futures = {
                executor.submit(
                    self.client.search,
                    query=q,
                    search_depth=self.search_depth,
                    topic=self.topic,
                    max_results=per_query_limit,
                    include_answer=self.include_answer,
                    exclude_domains=EXCLUDE_DOMAINS,
                ): q
                for q in queries
            }
            for future in as_completed(futures):
                try:
                    responses.append(future.result())
                except Exception:
                    # Skip failed queries
                    pass

        return merge_tavily_responses(responses)

    @property
    def client(self):
        if self._client is None:
            from tavily import TavilyClient
            if self.proxy_url:
                session = requests.Session()
                session.proxies.update({
                    "http": self.proxy_url,
                    "https": self.proxy_url,
                })
                self._client = TavilyClient(api_key=self.api_key, session=session)
            else:
                self._client = TavilyClient(api_key=self.api_key)
        return self._client


def format_tavily_response(query: str, response: dict[str, Any], max_items: int = 6) -> str:
    lines = [f"联网搜索：{query}"]

    answer = str(response.get("answer") or "").strip()
    if answer:
        lines.extend(["", answer])

    results = response.get("results") or []
    if not results:
        lines.extend(["", "未找到搜索结果。"])
        return "\n".join(lines).strip()

    lines.extend(["", "来源："])
    for index, item in enumerate(results[:max_items], start=1):
        title = str(item.get("title") or "Untitled").strip()
        url = str(item.get("url") or "").strip()
        content = str(item.get("content") or "").strip()
        source = urlparse(url).netloc
        if url:
            lines.append(f"{index}. 标题：[{title}]({url})")
        else:
            lines.append(f"{index}. 标题：{title}")
        if source:
            lines.append(f"   来源：{source}")
        if content:
            lines.append(f"   摘要：{content[:120]}")

    return "\n".join(lines).strip()


def build_search_queries(query: str) -> list[str]:
    """Hardcoded fallback for query expansion (used when LLM is unavailable)."""
    # Simple passthrough - let LLM handle complex expansion
    return [query]


def _normalize_url(url: str) -> str:
    """标准化 URL 用于去重：统一 https、去 www 前缀、去尾部斜杠。"""
    url = url.strip().rstrip("/")
    # 统一为 https
    url = url.replace("http://", "https://", 1)
    # 去 www. 前缀
    parsed = urlparse(url)
    host = parsed.hostname or ""
    if host.startswith("www."):
        host = host[4:]
    path = parsed.path or "/"
    return f"{host}{path}".lower()


def merge_tavily_responses(responses: list[dict[str, Any]]) -> dict[str, Any]:
    answers = []
    results = []
    seen_urls = set()
    for response in responses:
        if response.get("answer"):
            answers.append(str(response["answer"]).strip())
        for item in response.get("results") or []:
            url = str(item.get("url") or "")
            key = _normalize_url(url)
            if not key or key in seen_urls:
                continue
            seen_urls.add(key)
            results.append(item)
    return {
        "answer": "\n".join(dict.fromkeys(answer for answer in answers if answer)),
        "results": results,
    }
