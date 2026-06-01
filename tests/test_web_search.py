import os
import unittest
from unittest.mock import patch

from web_search import TavilyWebSearch, format_tavily_response


class TavilyWebSearchTest(unittest.TestCase):
    def test_format_tavily_response_includes_answer_and_sources(self):
        text = format_tavily_response(
            "CVE-2026 test",
            {
                "answer": "这是搜索摘要。",
                "results": [
                    {
                        "title": "Vendor advisory CVE-2026 test vulnerability",
                        "url": "https://example.com/advisory",
                        "content": "A short advisory summary for an RCE vulnerability.",
                    }
                ],
            },
        )

        self.assertIn("联网搜索：CVE-2026 test", text)
        self.assertIn("这是搜索摘要。", text)
        self.assertIn("[Vendor advisory CVE-2026 test vulnerability](https://example.com/advisory)", text)
        self.assertIn("A short advisory summary for an RCE vulnerability.", text)

    def test_format_tavily_response_limits_results(self):
        text = format_tavily_response(
            "AcmeServer 漏洞",
            {
                "results": [
                    {"title": "AcmeServer RCE", "url": "https://example.com/a", "content": "first"},
                    {"title": "AcmeServer XSS", "url": "https://example.com/b", "content": "second"},
                    {"title": "AcmeServer SSRF", "url": "https://example.com/c", "content": "third"},
                ],
            },
            max_items=2,
        )

        self.assertIn("https://example.com/a", text)
        self.assertIn("https://example.com/b", text)
        self.assertNotIn("https://example.com/c", text)

    def test_search_report_uses_llm_for_query_expansion_and_reranking(self):
        class FakeClient:
            calls = []

            def search(self, **kwargs):
                self.calls.append(kwargs["query"])
                return {
                    "results": [{
                        "title": f"Result for {kwargs['query']}",
                        "url": f"https://example.com/{kwargs['query']}",
                        "content": "Vulnerability details",
                    }]
                }

        class LLMSummarizer:
            def expand_search_queries(self, query, max_queries=5):
                return [
                    "TongWeb EJB反序列化漏洞",
                    "TongWeb 远程代码执行 CVE",
                    "东方通 TongWeb 安全公告",
                ]

            def rerank_results(self, query, results, top_k=6):
                for result in results:
                    result["relevance_score"] = 9.0
                return results[:top_k]

            def summarize_search_results(self, query, response, max_items=6):
                return f"联网搜索：{query}\n\n1. 标题：TongWeb EJB反序列化\n   来源：example.com\n   链接：https://example.com\n   摘要：EJB反序列化漏洞"

        client = FakeClient()
        summarizer = LLMSummarizer()
        searcher = TavilyWebSearch(
            api_key="tvly-test",
            max_results=10,
            result_summarizer=summarizer,
            _client=client,
        )

        text = searcher.search_report("TongWeb安全漏洞")

        self.assertIn("TongWeb EJB反序列化漏洞", client.calls)
        self.assertIn("TongWeb 远程代码执行 CVE", client.calls)
        self.assertIn("东方通 TongWeb 安全公告", client.calls)
        self.assertIn("EJB反序列化", text)

    def test_search_report_falls_back_to_single_query_without_llm(self):
        class FakeClient:
            calls = []

            def search(self, **kwargs):
                self.calls.append(kwargs["query"])
                return {
                    "results": [{
                        "title": "Result",
                        "url": "https://example.com",
                        "content": "Content",
                    }]
                }

        client = FakeClient()
        searcher = TavilyWebSearch(
            api_key="tvly-test",
            report_max_items=6,
            _client=client,
        )

        text = searcher.search_report("TongWeb安全漏洞")

        self.assertEqual(client.calls, ["TongWeb安全漏洞"])
        self.assertIn("联网搜索：TongWeb安全漏洞", text)

    def test_search_report_handles_llm_query_expansion_failure(self):
        class FakeClient:
            def search(self, **kwargs):
                return {
                    "results": [{
                        "title": "Fallback result",
                        "url": "https://example.com",
                        "content": "Content",
                    }]
                }

        class FailingSummarizer:
            def expand_search_queries(self, query, max_queries=5):
                raise Exception("LLM API error")

            def rerank_results(self, query, results, top_k=6):
                return results

            def summarize_search_results(self, query, response, max_items=6):
                return "Report"

        summarizer = FailingSummarizer()
        searcher = TavilyWebSearch(
            api_key="tvly-test",
            result_summarizer=summarizer,
            _client=FakeClient(),
        )

        text = searcher.search_report("TongWeb安全漏洞")
        self.assertIn("Report", text)

    def test_search_report_handles_llm_reranking_failure(self):
        class FakeClient:
            def search(self, **kwargs):
                return {
                    "results": [{
                        "title": "Result",
                        "url": "https://example.com",
                        "content": "Content",
                    }]
                }

        class FailingReranker:
            def expand_search_queries(self, query, max_queries=5):
                return ["Query 1", "Query 2"]

            def rerank_results(self, query, results, top_k=6):
                raise Exception("LLM API error")

            def summarize_search_results(self, query, response, max_items=6):
                return "Report"

        summarizer = FailingReranker()
        searcher = TavilyWebSearch(
            api_key="tvly-test",
            result_summarizer=summarizer,
            _client=FakeClient(),
        )

        text = searcher.search_report("TongWeb安全漏洞")
        self.assertIn("Report", text)

    def test_from_config_reads_tavily_api_key_environment(self):
        with patch.dict(os.environ, {"TAVILY_API_KEY": "tvly-test"}):
            searcher = TavilyWebSearch.from_config({
                "proxy": {
                    "url": "http://127.0.0.1:7890",
                    "web_search": True,
                },
                "web_search": {
                    "enabled": True,
                    "api_key_env": "TAVILY_API_KEY",
                    "max_results": 3,
                    "search_depth": "advanced",
                    "topic": "news",
                }
            })

        self.assertIsNotNone(searcher)
        self.assertEqual(searcher.api_key, "tvly-test")
        self.assertEqual(searcher.max_results, 3)
        self.assertEqual(searcher.search_depth, "advanced")
        self.assertEqual(searcher.topic, "news")
        self.assertEqual(searcher.proxy_url, "http://127.0.0.1:7890")


if __name__ == "__main__":
    unittest.main()
