import asyncio
import tempfile
import unittest
from datetime import date
from pathlib import Path

from report import ReportStore
from wecom_ai_bot import (
    WeComAIBotRunner,
    extract_chat_id,
    extract_sender_id,
    extract_text,
    is_private_chat,
    is_web_search_command,
    normalize_command,
)


class FakeClient:
    def __init__(self):
        self.events = {}
        self.replies = []
        self.sent = []
        self.connected = False

    def on(self, event, handler):
        self.events[event] = handler
        return self

    async def connect(self):
        self.connected = True
        return self

    async def reply_stream(self, frame, stream_id, content, finish=False):
        self.replies.append((frame, stream_id, content, finish))

    async def send_message(self, chatid, body):
        self.sent.append((chatid, body))


class WeComAIBotRunnerTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        (root / "today.md").write_text(
            """# 每日安全资讯（2026-05-28）

- Exploit-DB.com RSS Feed
  - [[webapps] test RCE](https://example.com/rce)
""",
            encoding="utf-8",
        )
        self.store = ReportStore(root, today=date(2026, 5, 28))

    def tearDown(self):
        self.tmp.cleanup()

    def test_extracts_text_and_chat_id_from_frame(self):
        frame = {
            "body": {
                "chatid": "chat-1",
                "text": {"content": "今日安全情报"},
            }
        }

        self.assertEqual(extract_chat_id(frame), "chat-1")
        self.assertEqual(extract_text(frame), "今日安全情报")

    def test_is_private_chat_when_no_chatid(self):
        # 群聊帧：包含 chatid
        group_frame = {"body": {"chatid": "chat-1", "text": {"content": "hi"}}}
        self.assertFalse(is_private_chat(group_frame))

        # 私聊帧：不含 chatid，只有 from.userid
        private_frame = {
            "body": {
                "from": {"userid": "zhangsan"},
                "text": {"content": "你好"},
            }
        }
        self.assertTrue(is_private_chat(private_frame))

        # 空帧也视为私聊（无 chatid）
        self.assertTrue(is_private_chat({"body": {}}))

    def test_extracts_sender_id_from_private_chat_frame(self):
        frame = {"body": {"from": {"userid": "zhangsan"}}}
        self.assertEqual(extract_sender_id(frame), "zhangsan")

        # 兼容不同 key 写法
        self.assertEqual(extract_sender_id({"body": {"from": {"user_id": "lisi"}}}), "lisi")
        self.assertEqual(extract_sender_id({"body": {"sender": {"id": "wangwu"}}}), "wangwu")
        self.assertEqual(extract_sender_id({"body": {}}), "")

    def test_is_web_search_command(self):
        # 应匹配联网搜索命令
        self.assertTrue(is_web_search_command("联网搜索 CVE-2026"))
        self.assertTrue(is_web_search_command("搜索 TongWeb 漏洞"))
        self.assertTrue(is_web_search_command("查找 RCE 漏洞"))
        self.assertTrue(is_web_search_command("查询 Log4j"))

        # 不应匹配其他命令
        self.assertFalse(is_web_search_command("今日安全情报"))
        self.assertFalse(is_web_search_command("最近3天"))
        self.assertFalse(is_web_search_command("关键词 RCE"))
        self.assertFalse(is_web_search_command("帮助"))

    def test_normalizes_mentioned_id_command(self):
        self.assertEqual(normalize_command("@安全机器人 ID"), "ID")
        self.assertEqual(normalize_command("@安全机器人\u2005ID"), "ID")
        self.assertEqual(normalize_command("@安全机器人：今日安全情报"), "今日安全情报")
        self.assertEqual(normalize_command("\u200b@安全机器人\u200b 今日安全情报"), "今日安全情报")
        self.assertEqual(normalize_command("@安全机器人\n今日安全情报"), "今日安全情报")
        self.assertEqual(normalize_command("@安全机器人今日安全情报"), "今日安全情报")
        self.assertEqual(normalize_command("@安全机器人最近3天"), "最近3天")
        self.assertEqual(normalize_command("@安全机器人关键词 RCE"), "关键词 RCE")
        self.assertEqual(normalize_command("@安全机器人搜索tongweb相关漏洞"), "搜索tongweb相关漏洞")
        self.assertEqual(normalize_command("@安全机器人\u2028今日安全情报"), "今日安全情报")
        self.assertEqual(normalize_command("@安全机器人\u2060关键词 RCE"), "关键词 RCE")
        self.assertEqual(normalize_command("复制文本 @安全机器人 今日安全情报"), "今日安全情报")

    def test_mobile_mention_command_reaches_today_report(self):
        client = FakeClient()
        runner = WeComAIBotRunner(client, self.store, allowed_chats=set())

        asyncio.run(runner.handle_text({"body": {"chatid": "phone", "text": {"content": "\u200b@安全机器人：今日安全情报"}}}))

        self.assertEqual(len(client.replies), 1)
        self.assertIn("test RCE", client.replies[0][2])

    def test_nonempty_whitelist_ignores_other_chat(self):
        client = FakeClient()
        runner = WeComAIBotRunner(client, self.store, allowed_chats={"chat-1"})

        asyncio.run(runner.handle_text({"body": {"chatid": "other", "text": {"content": "今日安全情报"}}}))

        self.assertEqual(client.replies, [])

    def test_empty_whitelist_allows_any_chat(self):
        client = FakeClient()
        runner = WeComAIBotRunner(client, self.store, allowed_chats=set())

        asyncio.run(runner.handle_text({"body": {"chatid": "other", "text": {"content": "今日安全情报"}}}))

        self.assertEqual(len(client.replies), 1)
        self.assertIn("test RCE", client.replies[0][2])

    def test_id_command_bypasses_whitelist_when_mentioned(self):
        client = FakeClient()
        runner = WeComAIBotRunner(client, self.store, allowed_chats={"chat-1"})

        asyncio.run(runner.handle_text({"body": {"chatid": "other", "text": {"content": "@安全机器人 ID"}}}))

        self.assertEqual(len(client.replies), 1)
        self.assertIn("other", client.replies[0][2])

    def test_dump_command_reports_body_keys_for_diagnostics(self):
        client = FakeClient()
        runner = WeComAIBotRunner(client, self.store, allowed_chats=set())

        asyncio.run(runner.handle_text({"body": {"chatId": "camel-chat", "text": {"content": "dump"}, "sender": {"id": "u1"}}}))

        self.assertEqual(len(client.replies), 1)
        self.assertIn("chatId", client.replies[0][2])
        self.assertIn("camel-chat", client.replies[0][2])

    def test_dump_triggers_even_when_mobile_mention_is_not_normalized(self):
        client = FakeClient()
        runner = WeComAIBotRunner(client, self.store, allowed_chats=set())

        asyncio.run(runner.handle_text({"body": {"chatid": "phone", "text": {"content": "@安全机器人dump"}}}))

        self.assertEqual(len(client.replies), 1)
        self.assertIn("body keys:", client.replies[0][2])

    def test_replies_to_whitelisted_chat_command(self):
        client = FakeClient()
        runner = WeComAIBotRunner(client, self.store, allowed_chats={"chat-1"})

        asyncio.run(runner.handle_text({"body": {"chatid": "chat-1", "text": {"content": "今日安全情报"}}}))

        self.assertEqual(len(client.replies), 1)
        self.assertIn("test RCE", client.replies[0][2])
        self.assertTrue(client.replies[0][3])

    def test_unknown_text_uses_llm_router_when_enabled(self):
        class FakeRouter:
            text = ""

            def route(self, text):
                self.text = text
                return type("Route", (), {"action": "today", "value": ""})()

        client = FakeClient()
        router = FakeRouter()
        runner = WeComAIBotRunner(client, self.store, allowed_chats=set(), llm_router=router)

        asyncio.run(runner.handle_text({"body": {"chatid": "chat-1", "text": {"content": "今天有什么重要漏洞"}}}))

        self.assertEqual(len(client.replies), 1)
        self.assertEqual(router.text, "今天有什么重要漏洞")
        self.assertIn("test RCE", client.replies[0][2])

    def test_runner_passes_llm_router_to_web_search(self):
        class FakeRouter:
            def route(self, text):
                return type("Route", (), {"action": "web_search", "value": "TongWeb 漏洞 CVE"})()

        class FakeWebSearch:
            result_summarizer = None

            def search_report(self, query):
                return f"search:{query}:summarizer={self.result_summarizer is not None}"

        client = FakeClient()
        runner = WeComAIBotRunner(
            client,
            self.store,
            allowed_chats=set(),
            llm_router=FakeRouter(),
            web_search=FakeWebSearch(),
        )

        asyncio.run(runner.handle_text({"body": {"chatid": "chat-1", "text": {"content": "搜索tongweb相关漏洞"}}}))

        # 第一条是进度提示，第二条是搜索结果
        self.assertEqual(len(client.replies), 2)
        self.assertIn("正在联网搜索", client.replies[0][2])
        self.assertIn("search:TongWeb 漏洞 CVE:summarizer=True", client.replies[1][2])

    def test_attached_mention_unknown_text_can_reach_llm_router(self):
        class FakeRouter:
            text = ""

            def route(self, text):
                self.text = text
                return type("Route", (), {"action": "today", "value": ""})()

        client = FakeClient()
        router = FakeRouter()
        runner = WeComAIBotRunner(client, self.store, allowed_chats=set(), llm_router=router)

        asyncio.run(runner.handle_text({"body": {"chatid": "chat-1", "text": {"content": "@安全机器人今天有什么重要漏洞"}}}))

        self.assertEqual(len(client.replies), 1)
        self.assertEqual(router.text, "安全机器人今天有什么重要漏洞")
        self.assertIn("test RCE", client.replies[0][2])

    def test_daily_push_sends_markdown_to_allowed_chats(self):
        client = FakeClient()
        runner = WeComAIBotRunner(client, self.store, allowed_chats={"chat-1", "chat-2"})

        asyncio.run(runner.push_daily())

        self.assertEqual([item[0] for item in client.sent], ["chat-1", "chat-2"])
        self.assertEqual(client.sent[0][1]["msgtype"], "markdown")
        self.assertIn("test RCE", client.sent[0][1]["markdown"]["content"])

    def test_private_chat_replies_via_send_message(self):
        """私聊：使用 send_message 回复，目标为发送者的 userid。"""
        client = FakeClient()
        runner = WeComAIBotRunner(client, self.store, allowed_chats=set())

        asyncio.run(runner.handle_text({
            "body": {
                "from": {"userid": "zhangsan"},
                "text": {"content": "今日安全情报"},
            }
        }))

        # 不应通过 reply_stream 回复
        self.assertEqual(client.replies, [])
        # 应通过 send_message 回复给发送者
        self.assertEqual(len(client.sent), 1)
        self.assertEqual(client.sent[0][0], "zhangsan")
        self.assertEqual(client.sent[0][1]["msgtype"], "markdown")
        self.assertIn("test RCE", client.sent[0][1]["markdown"]["content"])

    def test_private_chat_bypasses_allowed_chats(self):
        """私聊不受 allowed_chats 白名单限制。"""
        client = FakeClient()
        runner = WeComAIBotRunner(client, self.store, allowed_chats={"group-only"})

        asyncio.run(runner.handle_text({
            "body": {
                "from": {"userid": "zhangsan"},
                "text": {"content": "今日安全情报"},
            }
        }))

        # 私聊消息应该正常回复，即使 chatid 不在白名单中
        self.assertEqual(len(client.sent), 1)
        self.assertEqual(client.sent[0][0], "zhangsan")

    def test_private_chat_without_sender_id_does_not_crash(self):
        """私聊帧缺少发送者 ID 时，跳过回复但不崩溃。"""
        client = FakeClient()
        runner = WeComAIBotRunner(client, self.store, allowed_chats=set())

        asyncio.run(runner.handle_text({
            "body": {
                "text": {"content": "今日安全情报"},
            }
        }))

        # 无 sender_id，不应调用 reply_stream 或 send_message
        self.assertEqual(client.replies, [])
        self.assertEqual(client.sent, [])

    def test_web_search_sends_progress_message_in_group_chat(self):
        """联网搜索命令在群聊中先发送进度提示。"""
        client = FakeClient()

        class FakeWebSearch:
            def search_report(self, query):
                return f"搜索结果：{query}"

        runner = WeComAIBotRunner(
            client,
            self.store,
            allowed_chats=set(),
            web_search=FakeWebSearch(),
        )

        asyncio.run(runner.handle_text({
            "body": {
                "chatid": "chat-1",
                "text": {"content": "联网搜索 CVE-2026"},
            }
        }))

        # 应该有 2 次 reply_stream：进度提示 + 搜索结果
        self.assertEqual(len(client.replies), 2)
        self.assertIn("正在联网搜索", client.replies[0][2])
        self.assertIn("搜索结果", client.replies[1][2])

    def test_web_search_sends_progress_message_in_private_chat(self):
        """联网搜索命令在私聊中先发送进度提示。"""
        client = FakeClient()

        class FakeWebSearch:
            def search_report(self, query):
                return f"搜索结果：{query}"

        runner = WeComAIBotRunner(
            client,
            self.store,
            allowed_chats=set(),
            web_search=FakeWebSearch(),
        )

        asyncio.run(runner.handle_text({
            "body": {
                "from": {"userid": "zhangsan"},
                "text": {"content": "搜索 TongWeb 漏洞"},
            }
        }))

        # 应该有 2 次 send_message：进度提示 + 搜索结果
        self.assertEqual(len(client.sent), 2)
        # 进度提示使用 markdown 类型（send_message 不支持 text）
        self.assertEqual(client.sent[0][0], "zhangsan")
        self.assertEqual(client.sent[0][1]["msgtype"], "markdown")
        self.assertIn("正在联网搜索", client.sent[0][1]["markdown"]["content"])
        # 搜索结果使用 markdown 类型
        self.assertEqual(client.sent[1][0], "zhangsan")
        self.assertEqual(client.sent[1][1]["msgtype"], "markdown")
        self.assertIn("搜索结果", client.sent[1][1]["markdown"]["content"])


if __name__ == "__main__":
    unittest.main()
