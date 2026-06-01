#!/usr/bin/python3

import json
import os
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

import requests


SUPPORTED_ACTIONS = {"help", "id", "today", "recent", "keyword", "refresh", "web_search"}


@dataclass(frozen=True)
class LLMRoute:
    action: str
    value: str = ""

    def is_supported(self) -> bool:
        return self.action in SUPPORTED_ACTIONS


class LLMCommandRouter:
    def __init__(
        self,
        api_key: str,
        base_url: str,
        model: str,
        timeout: int = 90,
    ) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout

    @classmethod
    def from_config(cls, config: dict[str, Any]) -> "LLMCommandRouter | None":
        llm_conf = config.get("llm", {})
        if not llm_conf.get("enabled", False):
            return None

        api_key_env = llm_conf.get("api_key_env", "LLM_API_KEY")
        base_url_env = llm_conf.get("base_url_env", "LLM_BASE_URL")
        model_env = llm_conf.get("model_env", "LLM_MODEL")

        api_key = os.getenv(api_key_env) or llm_conf.get("api_key", "")
        base_url = os.getenv(base_url_env) or llm_conf.get("base_url", "")
        model = os.getenv(model_env) or llm_conf.get("model", "")
        if not api_key or not base_url or not model:
            raise RuntimeError(f"LLM 已启用，请设置 {api_key_env}、{base_url_env} 和 {model_env}")

        return cls(
            api_key=api_key,
            base_url=base_url,
            model=model,
            timeout=int(llm_conf.get("timeout", 90)),
        )

    def route(self, text: str) -> LLMRoute:
        content = self._chat(self._system_prompt(), text.strip())
        return self._parse_route(content)

    def summarize_search_results(
        self,
        query: str,
        response: dict[str, Any],
        max_items: int = 6,
    ) -> str:
        payload = {
            "query": query,
            "max_items": max_items,
            "answer": response.get("answer", ""),
            "results": self._compact_results(response.get("results") or []),
        }
        return self._chat(
            self._search_report_prompt(max_items),
            json.dumps(payload, ensure_ascii=False),
        ).strip()

    def expand_search_queries(
        self,
        query: str,
        max_queries: int = 5,
    ) -> list[str]:
        """Generate complementary search queries using domain knowledge."""
        payload = {
            "original_query": query,
            "max_queries": max_queries,
        }
        response = self._chat(
            self._query_expansion_prompt(max_queries),
            json.dumps(payload, ensure_ascii=False),
        )
        return self._parse_query_list(response)

    def rerank_results(
        self,
        query: str,
        results: list[dict[str, Any]],
        top_k: int = 10,
    ) -> list[dict[str, Any]]:
        """Score and rerank results by relevance."""
        compact = self._compact_results(results[:20])  # Limit to top 20 for cost
        payload = {
            "query": query,
            "top_k": top_k,
            "results": compact,
        }
        response = self._chat(
            self._rerank_prompt(top_k),
            json.dumps(payload, ensure_ascii=False),
        )
        scored = self._parse_scored_results(response)
        # Merge scores back into original results
        url_to_score = {item["url"]: item["score"] for item in scored}
        reranked = []
        for result in results:
            url = str(result.get("url") or "").strip()
            if url in url_to_score:
                result_copy = dict(result)
                result_copy["relevance_score"] = url_to_score[url]
                reranked.append(result_copy)
        reranked.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
        return reranked[:top_k]

    @staticmethod
    def _query_expansion_prompt(max_queries: int) -> str:
        return f"""你是网络安全研究员。将用户查询扩展为 {max_queries} 个互补的搜索查询。

要求：
- 覆盖不同漏洞类型（RCE、反序列化、XSS、SQL注入、文件上传、供应链攻击等）
- 包含中英文术语（CVE、CNVD、CNNVD、Exploit-DB、PoC）
- 考虑产品的技术栈（如中间件→Java EE/EJB/Servlet，Web框架→模板注入/SSRF）
- 包含官方公告和社区分析
- 如果查询包含具体产品，补充其常见组件或框架
- 如果查询过于宽泛，聚焦到具体漏洞类型

输出 JSON：
{{
  "queries": [
    "查询1",
    "查询2"
  ]
}}

只输出 JSON，不要解释。"""

    @staticmethod
    def _rerank_prompt(top_k: int) -> str:
        return f"""你是安全漏洞情报分析员。对搜索结果按相关性评分（0-10分）。

首先，根据查询内容识别查询中涉及的产品或厂商，然后判断哪个域名是该产品的官方网站或官方安全公告页面（如厂商官网、厂商安全响应中心）。来自这些官方域名的结果必须给予最高评分（10分），无论内容详略程度，因为官方信息是最权威的第一手来源。

评分标准：
- 10：厂商官方网站发布的安全公告、补丁通知、漏洞响应页面
- 9-10：权威漏洞数据库（CNVD、CNNVD、NVD、CVE）或安全社区（奇安信、长亭等）发布的详细漏洞分析
- 7-8：相关漏洞分析，但非目标产品或细节较少
- 4-6：边缘相关（提及产品但非漏洞，或通用安全文章）
- 0-3：无关内容（广告、招聘、教程、登录页）

要求：
- 官方来源必须保留：识别查询中的产品/厂商后，其官方网站的所有相关结果都要保留，不得丢弃
- 优先保留：厂商公告、CVE/NVD/CNVD/CNNVD、Exploit-DB、漏洞分析、PoC
- 保留社区分析：论坛、博客、GitHub 文章，只要涉及目标产品漏洞
- 去重：相同事件的不同来源只保留最可信的一条
- 最多保留 {top_k} 条

输出 JSON：
{{
  "ranked": [
    {{
      "url": "https://...",
      "score": 10,
      "reason": "厂商官方安全公告，第一手漏洞响应信息"
    }}
  ]
}}

只输出 JSON，不要解释。"""

    @staticmethod
    def _parse_query_list(response: str) -> list[str]:
        response = response.strip()
        if response.startswith("```"):
            response = response.strip("`")
            response = response.removeprefix("json").strip()
        try:
            data = json.loads(response)
            queries = data.get("queries", [])
            return [str(q).strip() for q in queries if str(q).strip()]
        except (json.JSONDecodeError, AttributeError):
            return []

    @staticmethod
    def _parse_scored_results(response: str) -> list[dict[str, Any]]:
        response = response.strip()
        if response.startswith("```"):
            response = response.strip("`")
            response = response.removeprefix("json").strip()
        try:
            data = json.loads(response)
            ranked = data.get("ranked", [])
            return [
                {
                    "url": str(item.get("url") or "").strip(),
                    "score": float(item.get("score", 0)),
                    "reason": str(item.get("reason") or "").strip(),
                }
                for item in ranked
                if item.get("url")
            ]
        except (json.JSONDecodeError, AttributeError, ValueError):
            return []

    def _chat(self, system_prompt: str, user_content: str) -> str:
        payload = {
            "model": self.model,
            "temperature": 0,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
        }
        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]

    @staticmethod
    def _compact_results(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
        compacted = []
        for item in results[:12]:
            url = str(item.get("url") or "").strip()
            compacted.append({
                "title": str(item.get("title") or "").strip(),
                "source": urlparse(url).netloc,
                "url": url,
                "content": str(item.get("content") or item.get("raw_content") or "").strip()[:800],
                "score": item.get("score"),
            })
        return compacted

    @staticmethod
    def _parse_route(content: str) -> LLMRoute:
        content = content.strip()
        if content.startswith("```"):
            content = content.strip("`")
            content = content.removeprefix("json").strip()
        data = json.loads(content)
        route = LLMRoute(
            action=str(data.get("action", "")).strip().lower(),
            value=str(data.get("value", "")).strip(),
        )
        if not route.is_supported():
            return LLMRoute("help")
        return route

    @staticmethod
    def _system_prompt() -> str:
        return """你是安全情报 Bot 的意图解析器，只能输出 JSON，不要输出解释。
把用户自然语言映射到一个本地动作：
- help：用户询问可用命令、用法，或意图不明确
- id：用户询问当前群/会话 ID
- today：用户要今天、今日、当天安全情报
- recent：用户要最近 N 天安全情报，value 填数字；默认 3
- keyword：用户要搜索漏洞、厂商、CVE、RCE 等关键词，value 填关键词
- refresh：用户明确要求重新抓取、刷新 RSS、更新今日情报
- web_search：用户明确要求联网搜索、查最新外部网页信息，value 填扩展后的搜索关键词。扩展时保留核心实体，补充常见漏洞词，例如 CVE、漏洞、RCE、SQL 注入、CNVD、NVD、Exploit-DB、厂商公告；不要完整照抄用户原句。

输出格式必须是：
{"action":"today","value":""}
或：
{"action":"recent","value":"3"}
或：
{"action":"web_search","value":"CVE-2026 最新利用"}
"""

    @staticmethod
    def _search_report_prompt(max_items: int) -> str:
        return f"""你是安全漏洞情报分析员。请把 Tavily 搜索结果整理成中文短报告。
要求：
- 去重：相同链接、相同标题、同一事件的重复转载只保留最可信的一条。
- 过滤：只删除明确无关、广告、登录页、无标题页、招聘、营销、泛泛教程；不要因为来源不是权威就删除。
- 保留：只要标题或摘要同时包含目标产品和漏洞/RCE/命令执行/XSS/文件上传/反序列化/CVE/CNVD/QVD 等安全词，就应保留。
- 优先：厂商公告、CVE/NVD/CNVD/CNNVD、Exploit-DB、漏洞分析、PoC/利用说明。
- 社区来源：论坛、博客、微信公众号文章归档、GitHub 文章镜像只要涉及目标产品漏洞、利用方法、影响版本或修复建议，也应保留为补充。
- 覆盖：尽量覆盖不同漏洞类型、不同年份、不同来源，不要只保留 2-3 条。
- 最多保留 {max_items} 条，不要输出长篇原文。
- 按“标题、来源、链接、摘要”组织，摘要每条不超过 60 个中文字符。
- 如果没有可靠相关结果，直接说明“未找到可靠相关结果”。

输出格式：
联网搜索：<query>
结论：<一句话总结>

1. 标题：<title>
   来源：<domain>
   链接：<url>
   摘要：<why relevant>
"""
