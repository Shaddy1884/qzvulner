import os
import unittest
from unittest.mock import patch

from llm import LLMCommandRouter, LLMRoute


class LLMCommandRouterTest(unittest.TestCase):
    def test_disabled_config_returns_none(self):
        router = LLMCommandRouter.from_config({"llm": {"enabled": False}})

        self.assertIsNone(router)

    def test_from_config_reads_environment(self):
        with patch.dict(os.environ, {
            "LLM_API_KEY": "key",
            "LLM_BASE_URL": "https://example.com/v1",
            "LLM_MODEL": "model",
        }):
            router = LLMCommandRouter.from_config({"llm": {"enabled": True}})

        self.assertEqual(router.api_key, "key")
        self.assertEqual(router.base_url, "https://example.com/v1")
        self.assertEqual(router.model, "model")

    def test_default_timeout_is_long_enough_for_search_summarization(self):
        with patch.dict(os.environ, {
            "LLM_API_KEY": "key",
            "LLM_BASE_URL": "https://example.com/v1",
            "LLM_MODEL": "model",
        }):
            router = LLMCommandRouter.from_config({"llm": {"enabled": True}})

        self.assertGreaterEqual(router.timeout, 60)

    def test_parse_route_accepts_json_fence(self):
        route = LLMCommandRouter._parse_route('```json\n{"action":"recent","value":"7"}\n```')

        self.assertEqual(route, LLMRoute("recent", "7"))

    def test_parse_route_rejects_unknown_action(self):
        route = LLMCommandRouter._parse_route('{"action":"shell","value":"rm"}')

        self.assertEqual(route, LLMRoute("help", ""))

    def test_parse_route_accepts_web_search_action(self):
        route = LLMCommandRouter._parse_route('{"action":"web_search","value":"CVE-2026"}')

        self.assertEqual(route, LLMRoute("web_search", "CVE-2026"))

    def test_summarize_search_results_requests_concise_deduplicated_report(self):
        captured = {}

        class FakeResponse:
            def raise_for_status(self):
                return None

            def json(self):
                return {"choices": [{"message": {"content": "整理后的报告"}}]}

        def fake_post(url, headers, json, timeout):
            captured["payload"] = json
            return FakeResponse()

        router = LLMCommandRouter("key", "https://example.com/v1", "model")
        with patch("llm.requests.post", fake_post):
            text = router.summarize_search_results(
                "TongWeb 漏洞",
                {"results": [{"title": "TongWeb RCE", "url": "https://example.com/a", "content": "details"}]},
            )

        self.assertEqual(text, "整理后的报告")
        system = captured["payload"]["messages"][0]["content"]
        user = captured["payload"]["messages"][1]["content"]
        self.assertIn("去重", system)
        self.assertIn("过滤", system)
        self.assertIn("标题", system)
        self.assertIn("来源", system)
        self.assertIn("链接", system)
        self.assertIn("只删除明确无关", system)
        self.assertIn("不同漏洞类型", system)
        self.assertIn("TongWeb 漏洞", user)

    def test_expand_search_queries_generates_complementary_searches(self):
        captured = {}

        class FakeResponse:
            def raise_for_status(self):
                return None

            def json(self):
                return {"choices": [{"message": {"content": '{"queries": ["TongWeb EJB反序列化", "TongWeb RCE CVE", "东方通 TongWeb 安全公告"]}'}}]}

        def fake_post(url, headers, json, timeout):
            captured["payload"] = json
            return FakeResponse()

        router = LLMCommandRouter("key", "https://example.com/v1", "model")
        with patch("llm.requests.post", fake_post):
            queries = router.expand_search_queries("TongWeb安全漏洞", max_queries=5)

        self.assertEqual(len(queries), 3)
        self.assertIn("TongWeb EJB反序列化", queries)
        self.assertIn("TongWeb RCE CVE", queries)
        self.assertIn("东方通 TongWeb 安全公告", queries)
        system = captured["payload"]["messages"][0]["content"]
        self.assertIn("互补", system)
        self.assertIn("漏洞类型", system)

    def test_rerank_results_scores_by_relevance(self):
        captured = {}

        class FakeResponse:
            def raise_for_status(self):
                return None

            def json(self):
                return {"choices": [{"message": {"content": '{"ranked": [{"url": "https://example.com/a", "score": 9.5, "reason": "EJB反序列化漏洞"}, {"url": "https://example.com/b", "score": 7.0, "reason": "相关产品"}]}'}}]}

        def fake_post(url, headers, json, timeout):
            captured["payload"] = json
            return FakeResponse()

        router = LLMCommandRouter("key", "https://example.com/v1", "model")
        with patch("llm.requests.post", fake_post):
            results = router.rerank_results(
                "TongWeb漏洞",
                [
                    {"title": "TongWeb EJB", "url": "https://example.com/a", "content": "EJB"},
                    {"title": "TongWeb RCE", "url": "https://example.com/b", "content": "RCE"},
                ],
                top_k=2,
            )

        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["url"], "https://example.com/a")
        self.assertEqual(results[0]["relevance_score"], 9.5)
        self.assertEqual(results[1]["url"], "https://example.com/b")
        self.assertEqual(results[1]["relevance_score"], 7.0)
        system = captured["payload"]["messages"][0]["content"]
        self.assertIn("评分", system)
        self.assertIn("相关性", system)


if __name__ == "__main__":
    unittest.main()
