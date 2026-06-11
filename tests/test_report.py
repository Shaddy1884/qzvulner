import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

from report import ReportResult, ReportStore, execute_route, handle_command


SAMPLE_REPORT = """# 每日安全资讯（2026-05-28）

- Exploit-DB.com RSS Feed
  - [[webapps] scramble - RCE Remote Code Execution](https://www.exploit-db.com/exploits/52582)
- 字节跳动安全中心
  - [护航618 | 抖音电商安全专测开启](https://example.com/bytedance)
"""


class ReportStoreTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        archive = self.root / "archive" / "2026"
        archive.mkdir(parents=True)
        (self.root / "today.md").write_text(SAMPLE_REPORT, encoding="utf-8")
        (archive / "2026-05-28.md").write_text(SAMPLE_REPORT, encoding="utf-8")
        (archive / "2026-05-26.md").write_text(
            """# 每日安全资讯（2026-05-26）

- 绿盟科技技术博客
  - [某产品 RCE 漏洞分析](https://example.com/rce)
""",
            encoding="utf-8",
        )
        # today.md 日期是 2026-05-28，所以设置 self.today 为 2026-05-29
        # 这样 expected_date = 2026-05-28 才能匹配
        self.store = ReportStore(self.root, today=date(2026, 5, 29))

    def tearDown(self):
        self.tmp.cleanup()

    def test_today_uses_cached_today_file(self):
        text = self.store.today_report().text

        self.assertIn("每日安全资讯（2026-05-28）", text)
        self.assertIn("Remote Code Execution", text)

    def test_recent_skips_missing_archives_and_mentions_dates(self):
        text = self.store.recent_report(3)

        self.assertIn("2026-05-28", text)
        # 2026-05-29 和 2026-05-27 缺失
        self.assertIn("缺失归档：2026-05-29", text)
        self.assertIn("2026-05-27", text)

    def test_keyword_search_scans_all_archived_titles(self):
        text = self.store.keyword_report("RCE")

        self.assertIn("关键词：RCE", text)
        self.assertIn("2026-05-26", text)
        self.assertIn("某产品 RCE 漏洞分析", text)
        self.assertIn("Remote Code Execution", text)

    def test_keyword_search_does_not_match_source_names(self):
        text = self.store.keyword_report("Exploit")

        self.assertIn("未找到匹配", text)

    def test_ascii_keyword_search_does_not_match_inside_word(self):
        archive = self.root / "archive" / "2026" / "2026-05-27.md"
        archive.write_text(
            """# 每日安全资讯（2026-05-27）

- Test
  - [Fake software on SourceForge distribute Deno RAT](https://example.com/sourceforge)
""",
            encoding="utf-8",
        )

        text = self.store.keyword_report("RCE")

        self.assertNotIn("SourceForge", text)

    def test_empty_today_reports_no_news(self):
        # 创建空的 today.md，日期为昨天（2026-05-28）
        (self.root / "today.md").write_text("# 每日安全资讯（2026-05-28）\n\n", encoding="utf-8")

        text = self.store.today_report().text

        self.assertIn("今日暂无安全情报", text)

    def test_stale_today_warns_about_outdated_file(self):
        # today.md 日期是 2026-05-28，但今天已经是 2026-05-30
        # 期望的日期应该是 2026-05-29（昨天），实际是 2026-05-28（前天）
        store = ReportStore(self.root, today=date(2026, 5, 30))

        text = store.today_report().text

        self.assertIn("2026-05-30", text)
        self.assertIn("尚未更新", text)
        self.assertIn("2026-05-28", text)

    def test_today_report_defaults_to_beijing_yesterday(self):
        (self.root / "today.md").write_text(
            """# 每日安全资讯（2026-06-02）

- 测试源
  - [TongWeb 安全漏洞通报](https://example.com/tongweb)
""",
            encoding="utf-8",
        )

        with patch("report.beijing_today", return_value=date(2026, 6, 3)):
            store = ReportStore(self.root)
            text = store.today_report().text

        self.assertIn("每日安全资讯（2026-06-02）", text)
        self.assertIn("TongWeb 安全漏洞通报", text)
        self.assertNotIn("尚未更新", text)

    def test_today_report_default_still_warns_when_beijing_date_is_stale(self):
        (self.root / "today.md").write_text(
            """# 每日安全资讯（2026-06-01）

- 测试源
  - [旧日报](https://example.com/old)
""",
            encoding="utf-8",
        )

        with patch("report.beijing_today", return_value=date(2026, 6, 3)):
            store = ReportStore(self.root)
            text = store.today_report().text

        self.assertIn("尚未更新", text)
        self.assertIn("期望日期 2026-06-02", text)
        self.assertIn("实际日期 2026-06-01", text)

    def test_auto_refresh_enabled_when_today_not_injected(self):
        """未显式注入 today 时，_auto_refresh 为 True。"""
        store = ReportStore(self.root)
        self.assertTrue(store._auto_refresh)

    def test_auto_refresh_disabled_when_today_injected(self):
        """显式注入 today 后，_auto_refresh 为 False，不受外部日期影响。"""
        store = ReportStore(self.root, today=date(2026, 6, 3))
        self.assertFalse(store._auto_refresh)

    def test_maybe_refresh_updates_today_on_boundary_cross(self):
        """跨日后 _maybe_refresh_today 更新 self.today 为当前北京时间。"""
        with patch("report.beijing_today", side_effect=[date(2026, 6, 3), date(2026, 6, 4)]):
            store = ReportStore(self.root)  # today = 2026-06-03
            store._maybe_refresh_today()
            self.assertEqual(store.today, date(2026, 6, 4))

    def test_maybe_refresh_noop_when_today_injected(self):
        """注入 today 后 _maybe_refresh_today 是空操作，不覆盖注入值。"""
        store = ReportStore(self.root, today=date(2026, 6, 3))
        with patch("report.beijing_today", return_value=date(2026, 6, 4)):
            store._maybe_refresh_today()
            self.assertEqual(store.today, date(2026, 6, 3))

    def test_today_report_ready_false_when_file_missing(self):
        """today.md 不存在时 ready=False。"""
        (self.root / "today.md").unlink()
        result = self.store.today_report()
        self.assertFalse(result.ready)
        self.assertIn("今日暂无安全情报", result.text)

    def test_today_report_ready_false_when_stale(self):
        """today.md 日期过期时 ready=False。"""
        store = ReportStore(self.root, today=date(2026, 5, 30))
        result = store.today_report()
        self.assertFalse(result.ready)
        self.assertIn("尚未更新", result.text)

    def test_today_report_ready_true_when_normal(self):
        """today.md 日期匹配且内容有效时 ready=True。"""
        result = self.store.today_report()
        self.assertTrue(result.ready)
        self.assertIn("Remote Code Execution", result.text)

    def test_get_archive_report_ready_when_file_valid(self):
        """归档文件存在、日期匹配、有文章时 ready=True。"""
        result = self.store.get_archive_report("2026-05-28")
        self.assertTrue(result.ready)
        self.assertIn("Remote Code Execution", result.text)

    def test_get_archive_report_not_ready_when_file_missing(self):
        """归档文件不存在时 ready=False 并给出有用提示。"""
        result = self.store.get_archive_report("2026-05-27")
        self.assertFalse(result.ready)
        self.assertIn("不存在", result.text)

    def test_get_archive_report_not_ready_when_title_mismatch(self):
        """归档文件标题日期与文件名不匹配时 ready=False。"""
        archive = self.root / "archive" / "2026"
        (archive / "2026-05-25.md").write_text(
            "# 每日安全资讯（2026-05-24）\n\n"
            "- Test\n  - [Article](https://example.com)\n",
            encoding="utf-8",
        )
        result = self.store.get_archive_report("2026-05-25")
        self.assertFalse(result.ready)
        self.assertIn("不匹配", result.text)

    def test_get_archive_report_not_ready_when_invalid_date(self):
        """无效日期格式返回 ready=False。"""
        result = self.store.get_archive_report("not-a-date")
        self.assertFalse(result.ready)
        self.assertIn("格式错误", result.text)

    def test_get_archive_report_not_ready_when_no_articles(self):
        """归档文件日期正确但无文章时 ready=False。"""
        archive = self.root / "archive" / "2026"
        (archive / "2026-05-25.md").write_text(
            "# 每日安全资讯（2026-05-25）\n\n"
            "> 今日暂无收录安全资讯。\n",
            encoding="utf-8",
        )
        result = self.store.get_archive_report("2026-05-25")
        self.assertFalse(result.ready)
        self.assertIn("暂无安全情报", result.text)


class CommandHandlerTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        (root / "today.md").write_text(SAMPLE_REPORT, encoding="utf-8")
        self.store = ReportStore(root, today=date(2026, 5, 29))

    def tearDown(self):
        self.tmp.cleanup()

    def test_id_command_returns_conversation_id(self):
        text = handle_command("id", self.store, conversation_id="chat-123")

        self.assertIn("chat-123", text)

    def test_keyword_command_routes_to_archive_search(self):
        text = handle_command("关键词 RCE", self.store)

        self.assertIn("关键词：RCE", text)

    def test_web_search_command_routes_to_web_searcher(self):
        class FakeWebSearch:
            query = ""

            def search_report(self, query):
                self.query = query
                return "联网搜索结果"

        web_search = FakeWebSearch()
        text = handle_command("联网搜索 CVE-2026-0001", self.store, web_search=web_search)

        self.assertEqual(web_search.query, "CVE-2026-0001")
        self.assertEqual(text, "联网搜索结果")

    def test_natural_search_command_routes_to_web_searcher(self):
        class FakeWebSearch:
            query = ""

            def search_report(self, query):
                self.query = query
                return "联网搜索结果"

        web_search = FakeWebSearch()
        text = handle_command("搜索tongweb相关漏洞", self.store, web_search=web_search)

        self.assertEqual(web_search.query, "tongweb相关漏洞")
        self.assertEqual(text, "联网搜索结果")

    def test_natural_search_can_use_llm_expanded_query(self):
        class FakeRouter:
            text = ""

            def route(self, text):
                self.text = text
                return type("Route", (), {
                    "action": "web_search",
                    "value": "TongWeb 漏洞 CVE RCE site:cnvd.org.cn OR site:nvd.nist.gov",
                })()

        class FakeWebSearch:
            query = ""

            def search_report(self, query):
                self.query = query
                return "联网搜索结果"

        router = FakeRouter()
        web_search = FakeWebSearch()
        text = handle_command("搜索tongweb相关漏洞", self.store, llm_router=router, web_search=web_search)

        self.assertEqual(router.text, "搜索tongweb相关漏洞")
        self.assertEqual(web_search.query, "TongWeb 漏洞 CVE RCE site:cnvd.org.cn OR site:nvd.nist.gov")
        self.assertEqual(text, "联网搜索结果")

    def test_web_search_runtime_error_is_not_reported_as_llm_parse_failure(self):
        class FakeRouter:
            def route(self, text):
                return type("Route", (), {"action": "web_search", "value": "TongWeb 漏洞"})()

        class FailingWebSearch:
            def search_report(self, query):
                raise RuntimeError("Tavily 联网搜索失败：DNS 解析失败")

        text = handle_command(
            "搜索tongweb安全漏洞",
            self.store,
            llm_router=FakeRouter(),
            web_search=FailingWebSearch(),
        )

        self.assertIn("Tavily 联网搜索失败", text)
        self.assertNotIn("LLM 解析失败", text)

    def test_unknown_command_returns_help(self):
        text = handle_command("随便问问", self.store)

        self.assertIn("可用命令", text)

    def test_unknown_command_can_be_routed_by_llm(self):
        class FakeRouter:
            def route(self, text):
                self.text = text
                return type("Route", (), {"action": "keyword", "value": "RCE"})()

        router = FakeRouter()
        text = handle_command("帮我找一下远程代码执行漏洞", self.store, llm_router=router)

        self.assertEqual(router.text, "帮我找一下远程代码执行漏洞")
        self.assertIn("关键词：RCE", text)

    def test_execute_route_limits_recent_days(self):
        text = execute_route("recent", "60", self.store)

        self.assertIn("最近30天安全情报", text)

    def test_execute_route_can_use_web_search(self):
        class FakeWebSearch:
            def search_report(self, query):
                return f"web:{query}"

        text = execute_route("web_search", "Tavily", self.store, web_search=FakeWebSearch())

        self.assertEqual(text, "web:Tavily")


if __name__ == "__main__":
    unittest.main()
