#!/usr/bin/python3

"""
Diagnose the full Tavily + LLM search pipeline.

Shows every stage of the pipeline used by wecom_ai_bot.py:
  Stage 1 — Query expansion (LLM vs raw)
  Stage 2 — Parallel Tavily search results (per expanded query)
  Stage 3 — Merged & deduplicated results
  Stage 4 — LLM relevance reranking (with scores & reasons)
  Stage 5 — Final LLM-generated summary report
"""

import argparse
import json
import os
import time
from urllib.parse import urlparse

from llm import LLMCommandRouter
from web_search import EXCLUDE_DOMAINS, TavilyWebSearch, build_search_queries, merge_tavily_responses

import requests
requests.packages.urllib3.disable_warnings()


def print_section(title: str, char: str = "═") -> None:
    print(f"\n{char * 60}")
    print(f"  {title}")
    print(f"{char * 60}")


def print_results_table(results: list[dict], limit: int) -> None:
    for index, item in enumerate(results[:limit], start=1):
        item_title = str(item.get("title") or "Untitled").strip()
        url = str(item.get("url") or "").strip()
        source = urlparse(url).netloc if url else ""
        content = str(item.get("content") or "").strip().replace("\n", " ")
        print(f"  {index}. {item_title}")
        if source:
            print(f"     来源: {source}")
        if url:
            print(f"     链接: {url}")
        if content:
            print(f"     摘要: {content[:180]}")
        score = item.get("relevance_score")
        reason = item.get("_rerank_reason")
        if score is not None:
            line = f"     评分: {score:.1f}/10"
            if reason:
                line += f"  — {reason}"
            print(line)
        print()


def diagnose(query: str, config_path: str, search_depth: str, max_results: int, report_max_items: int) -> None:
    root = os.path.dirname(os.path.abspath(__file__))
    config_file = os.path.join(root, config_path) if not os.path.isabs(config_path) else config_path

    with open(config_file, encoding="utf-8") as f:
        config = json.load(f)

    # ── Initialise components ────────────────────────────────────────────
    llm_router = LLMCommandRouter.from_config(config)
    web_search = TavilyWebSearch.from_config(config)

    if not web_search:
        raise RuntimeError("web_search 未在 config.json 中启用 (web_search.enabled = true)")
    if not llm_router:
        raise RuntimeError("llm 未在 config.json 中启用 (llm.enabled = true)，无法诊断 LLM 聚合效果")

    if web_search.proxy_url:
        session = requests.Session()
        session.proxies.update({"http": web_search.proxy_url, "https": web_search.proxy_url})
        from tavily import TavilyClient
        tavily = TavilyClient(api_key=web_search.api_key, session=session)
    else:
        from tavily import TavilyClient
        tavily = TavilyClient(api_key=web_search.api_key)

    timings: dict[str, float] = {}

    print_section("诊断设置", "━")
    print(f"  查询: {query}")
    print(f"  search_depth: {search_depth}")
    print(f"  max_results: {max_results}")
    print(f"  report_max_items: {report_max_items}")
    print(f"  LLM model: {llm_router.model}")
    print(f"  LLM base_url: {llm_router.base_url}")

    # ── Stage 1: Query expansion ─────────────────────────────────────────
    print_section("Stage 1 — 查询扩展")
    raw_queries = build_search_queries(query)
    print(f"  硬编码 fallback: {raw_queries}")

    t0 = time.time()
    try:
        llm_queries = llm_router.expand_search_queries(query, max_queries=5)
    except Exception as exc:
        llm_queries = []
        print(f"  LLM 扩展失败: {exc}")
    timings["expand"] = time.time() - t0
    print(f"  LLM 扩展 ({len(llm_queries)} 条, {timings['expand']:.1f}s):")
    for q in llm_queries:
        print(f"    • {q}")

    search_queries = llm_queries if llm_queries else raw_queries

    # ── Stage 2: Parallel Tavily search ──────────────────────────────────
    print_section("Stage 2 — Tavily 原始搜索结果")
    per_query_limit = max(3, max_results // 2)
    all_responses: list[dict] = []
    t0 = time.time()

    for sq in search_queries:
        try:
            resp = tavily.search(
                query=sq,
                search_depth=search_depth,
                topic=web_search.topic,
                max_results=per_query_limit,
                include_answer=web_search.include_answer,
                exclude_domains=EXCLUDE_DOMAINS,
            )
            all_responses.append(resp)
            n = len(resp.get("results") or [])
            print(f"  ✓ {sq!r}  →  {n} results")
        except Exception as exc:
            print(f"  ✗ {sq!r}  →  FAILED: {exc}")
    timings["search"] = time.time() - t0

    print(f"\n  搜索总耗时: {timings['search']:.1f}s")

    for i, resp in enumerate(all_responses):
        results = resp.get("results") or []
        print(f"\n  ── Query {i + 1}: {search_queries[i]!r} ({len(results)} results) ──")
        print_results_table(results, max_results)

    # ── Stage 3: Merge & deduplicate ─────────────────────────────────────
    print_section("Stage 3 — 合并去重")
    merged = merge_tavily_responses(all_responses)
    total_raw = sum(len(r.get("results") or []) for r in all_responses)
    total_deduped = len(merged.get("results") or [])
    print(f"  原始结果数: {total_raw}")
    print(f"  去重后结果: {total_deduped}")

    answer = str(merged.get("answer") or "").strip()
    if answer:
        print(f"\n  Tavily Answer:")
        for line in answer.splitlines():
            print(f"    {line}")

    print(f"\n  去重后结果列表:")
    print_results_table(merged.get("results") or [], max_results)

    # ── Stage 4: LLM relevance reranking ─────────────────────────────────
    print_section("Stage 4 — LLM 相关性重排序")
    t0 = time.time()
    reranked: list[dict] = []
    try:
        reranked = llm_router.rerank_results(
            query, merged.get("results") or [], top_k=report_max_items,
        )
        timings["rerank"] = time.time() - t0
        print(f"  重排序完成 ({len(reranked)} 条, {timings['rerank']:.1f}s):")
        print_results_table(reranked, report_max_items)
    except Exception as exc:
        timings["rerank"] = time.time() - t0
        print(f"  ✗ LLM 重排序失败 ({timings['rerank']:.1f}s): {exc}")
        reranked = (merged.get("results") or [])[:report_max_items]

    # ── Stage 5: LLM summary report ──────────────────────────────────────
    print_section("Stage 5 — LLM 聚合报告")
    report_response = {
        "answer": merged.get("answer", ""),
        "results": reranked,
    }
    t0 = time.time()
    try:
        report = llm_router.summarize_search_results(query, report_response, max_items=report_max_items)
        timings["report"] = time.time() - t0
        print(f"  生成完成 ({timings['report']:.1f}s)\n")
        print("─" * 60)
        print(report)
        print("─" * 60)
    except Exception as exc:
        timings["report"] = time.time() - t0
        print(f"  ✗ LLM 报告生成失败 ({timings['report']:.1f}s): {exc}")

    # ── Summary ──────────────────────────────────────────────────────────
    print_section("耗时汇总", "━")
    total = sum(timings.values())
    for stage, seconds in timings.items():
        print(f"  {stage:>8}: {seconds:.1f}s")
    print(f"  {'TOTAL':>8}: {total:.1f}s")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="诊断 Tavily + LLM 搜索管线：展示从查询扩展到最终报告的每个阶段",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
示例:
  python3 diagnose_tavily.py "TongWeb安全漏洞"
  python3 diagnose_tavily.py "CVE-2026" --search-depth advanced
  python3 diagnose_tavily.py "Spring RCE" --report-max-items 8
""",
    )
    parser.add_argument("query", nargs="?", default="产品安全漏洞",
                        help="搜索查询 (默认: 产品安全漏洞)")
    parser.add_argument("--config", default="config.json",
                        help="配置文件路径 (默认: config.json)")
    parser.add_argument("--max-results", type=int, default=10,
                        help="每个查询的最大结果数 (默认: 10)")
    parser.add_argument("--search-depth", default="basic", choices=["basic", "advanced"],
                        help="Tavily 搜索深度 (默认: basic)")
    parser.add_argument("--report-max-items", type=int, default=6,
                        help="最终报告保留的最大条目数 (默认: 6)")
    args = parser.parse_args()

    diagnose(
        query=args.query,
        config_path=args.config,
        search_depth=args.search_depth,
        max_results=args.max_results,
        report_max_items=args.report_max_items,
    )


if __name__ == "__main__":
    main()
