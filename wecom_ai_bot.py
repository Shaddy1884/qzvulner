#!/usr/bin/python3

import argparse
import asyncio
import json
import logging
import os
import re
import signal
import sys
import time
from pathlib import Path
from typing import Any

import schedule
from wecom_aibot_sdk import WSClient, generate_req_id

from llm import LLMCommandRouter
from report import ReportStore, handle_command
from web_search import TavilyWebSearch

logger = logging.getLogger("wecom_ai_bot")


MAX_MESSAGE_CHARS = 3500
COMMAND_PATTERNS = [
    r"关键词\s+.+",
    r"最近\d+天",
    r"今日安全情报",
    r"联网搜索\s+.+",
    r"(?:搜索|查找|查询)\s*.+",
    r"刷新今日",
    r"帮助",
    r"(?<![A-Za-z0-9_])dump(?![A-Za-z0-9_])",
    r"(?<![A-Za-z0-9_])id(?![A-Za-z0-9_])",
]


def extract_chat_id(frame: dict[str, Any]) -> str:
    body = frame.get("body") or {}
    chat = body.get("chat") or {}
    conversation = body.get("conversation") or {}
    return (
        body.get("chatid")
        or body.get("chat_id")
        or body.get("chatId")
        or body.get("conversation_id")
        or body.get("conversationId")
        or chat.get("id")
        or chat.get("chatid")
        or chat.get("chatId")
        or conversation.get("id")
        or ""
    )


def is_private_chat(frame: dict[str, Any]) -> bool:
    """私聊（单聊）检测：群聊帧包含 chatid 类字段，私聊帧不包含。"""
    body = frame.get("body") or {}
    chat = body.get("chat") or {}
    conversation = body.get("conversation") or {}
    has_group_id = bool(
        body.get("chatid")
        or body.get("chat_id")
        or body.get("chatId")
        or body.get("conversation_id")
        or body.get("conversationId")
        or chat.get("id")
        or chat.get("chatid")
        or chat.get("chatId")
        or conversation.get("id")
    )
    return not has_group_id


def extract_sender_id(frame: dict[str, Any]) -> str:
    """从私聊帧中提取发送者 user ID，用于通过 send_message 回复私聊。"""
    body = frame.get("body") or {}
    from_user = body.get("from") or {}
    sender = body.get("sender") or {}
    return (
        from_user.get("userid")
        or from_user.get("user_id")
        or from_user.get("userId")
        or sender.get("userid")
        or sender.get("user_id")
        or sender.get("userId")
        or sender.get("id")
        or body.get("userid")
        or body.get("user_id")
        or body.get("userId")
        or ""
    )


def extract_text(frame: dict[str, Any]) -> str:
    body = frame.get("body") or {}
    text = body.get("text") or {}
    if isinstance(text, dict):
        return text.get("content", "")
    if isinstance(text, str):
        return text
    return ""


def normalize_command(text: str) -> str:
    command = re.sub(r"[\u200b\u200c\u200d\ufeff\u2060]", "", text).strip()
    found = _find_known_command(command)
    if found:
        return found
    if command.startswith("@"):
        command = command[1:]
        match = re.search(r"[\s:：]+", command)
        if not match:
            return command
        command = command[match.end():]
        command = command.lstrip(" \t\r\n:：")
    return command


def _find_known_command(text: str) -> str:
    for pattern in COMMAND_PATTERNS:
        if match := re.search(pattern, text, re.IGNORECASE):
            return match.group(0).strip()
    return ""


def is_web_search_command(command: str) -> bool:
    """检测命令是否为联网搜索（包括自然语言形式）。"""
    patterns = [
        r"^联网搜索\s+.+",
        r"^(?:搜索|查找|查询)\s*.+",
    ]
    return any(re.match(pattern, command, re.IGNORECASE) for pattern in patterns)


def split_message(text: str, limit: int = MAX_MESSAGE_CHARS) -> list[str]:
    if len(text) <= limit:
        return [text]

    chunks: list[str] = []
    current: list[str] = []
    current_size = 0
    for line in text.splitlines():
        line_size = len(line) + 1
        if current and current_size + line_size > limit:
            chunks.append("\n".join(current))
            current = []
            current_size = 0
        if line_size > limit:
            chunks.append(line[:limit])
            continue
        current.append(line)
        current_size += line_size
    if current:
        chunks.append("\n".join(current))
    return chunks


class WeComAIBotRunner:
    def __init__(
        self,
        client,
        store: ReportStore,
        allowed_chats: set[str],
        daily_push_time: str = "10:00",
        llm_router: LLMCommandRouter | None = None,
        web_search: TavilyWebSearch | None = None,
    ) -> None:
        self.client = client
        self.store = store
        self.allowed_chats = sorted(allowed_chats)
        self.daily_push_time = daily_push_time
        self.llm_router = llm_router
        self.web_search = web_search
        self._shutdown_event = asyncio.Event()
        if self.web_search and self.llm_router and not self.web_search.result_summarizer:
            self.web_search.result_summarizer = self.llm_router

    async def handle_text(self, frame: dict[str, Any]) -> None:
        chat_id = extract_chat_id(frame)
        text = extract_text(frame)
        command = normalize_command(text)
        diagnostic_requested = command.lower() == "dump" or bool(
            re.search(r"(?<![A-Za-z0-9_])dump(?![A-Za-z0-9_])", text, re.IGNORECASE)
        )
        private = is_private_chat(frame)

        if private:
            sender_id = extract_sender_id(frame)
            logger.info(f"[私聊] sender={sender_id or 'unknown'} command={command!r}")
        else:
            logger.info(f"[群聊] chat={chat_id or 'unknown'} command={command!r}")

        # 私聊（无 chatid）跳过 allowed_chats 过滤；群聊仍需匹配白名单
        if (
            self.allowed_chats
            and not private
            and command.lower() not in {"id", "dump"}
            and not diagnostic_requested
            and chat_id not in self.allowed_chats
        ):
            return

        # 联网搜索耗时较长，先发送进度提示
        if not diagnostic_requested and is_web_search_command(command) and self.web_search:
            await self.send_progress(frame, "🔍 正在联网搜索，请稍候...")

        t0 = time.time()
        response = self.diagnostic_dump(frame, chat_id) if diagnostic_requested else handle_command(
            command,
            self.store,
            conversation_id=chat_id,
            llm_router=self.llm_router,
            web_search=self.web_search,
        )
        elapsed = time.time() - t0
        await self.reply(frame, response)
        logger.info(f"命令处理完成: {command!r} ({elapsed:.1f}s, {len(response)} chars)")

    @staticmethod
    def diagnostic_dump(frame: dict[str, Any], chat_id: str) -> str:
        body = frame.get("body") or {}
        lines = [
            f"当前会话 ID：{chat_id or 'unknown'}",
            f"是否私聊：{'是' if is_private_chat(frame) else '否'}",
        ]
        if is_private_chat(frame):
            lines.append(f"发送者 ID：{extract_sender_id(frame) or 'unknown'}")
        lines.extend([
            "body keys: " + ", ".join(sorted(body.keys())),
            "body: " + json.dumps(body, ensure_ascii=False)[:1200],
        ])
        return "\n".join(lines)

    async def reply(self, frame: dict[str, Any], text: str) -> None:
        chunks = split_message(text)
        private = is_private_chat(frame)

        for index, chunk in enumerate(chunks):
            prefix = f"({index + 1}/{len(chunks)})\n" if len(chunks) > 1 else ""
            content = prefix + chunk

            if private:
                # 企业微信智能机器人 API：私聊（单聊）必须用 send_message
                # 并以发送者的 userid 作为目标；reply_stream 仅用于群聊上下文。
                sender_id = extract_sender_id(frame)
                if not sender_id:
                    logger.warning(
                        f"[私聊] 帧缺少发送者 ID，无法回复。"
                        f"body keys: {sorted((frame.get('body') or {}).keys())}"
                    )
                    continue
                await self.client.send_message(sender_id, {
                    "msgtype": "markdown",
                    "markdown": {"content": content},
                })
                logger.debug(f"[私聊] 已回复 sender={sender_id} ({len(content)} chars)")
            else:
                stream_id = generate_req_id("report")
                await self.client.reply_stream(frame, stream_id, content, True)
                chat_id = extract_chat_id(frame)
                logger.debug(f"[群聊] 已回复 chat={chat_id} ({len(content)} chars)")

    async def send_progress(self, frame: dict[str, Any], text: str) -> None:
        """发送进度提示消息（用于耗时操作如联网搜索）。"""
        private = is_private_chat(frame)
        if private:
            sender_id = extract_sender_id(frame)
            if not sender_id:
                logger.warning("[私聊] 帧缺少发送者 ID，无法发送进度提示")
                return
            await self.client.send_message(sender_id, {
                "msgtype": "markdown",
                "markdown": {"content": text},
            })
            logger.debug(f"[私聊] 已发送进度提示 sender={sender_id}")
        else:
            stream_id = generate_req_id("progress")
            await self.client.reply_stream(frame, stream_id, text, True)

    async def push_daily(self) -> None:
        result = self.store.today_report()
        if not result.ready:
            logger.warning("today.md 尚未就绪，跳过每日推送")
            return
        logger.info(f"开始推送每日安全情报，目标群: {len(self.allowed_chats)} 个")
        for chat_id in self.allowed_chats:
            for chunk in split_message(result.text):
                await self.client.send_message(chat_id, {
                    "msgtype": "markdown",
                    "markdown": {"content": chunk},
                })
            logger.info(f"已推送每日情报到群 {chat_id}")

    async def push_today_manual(self) -> bool:
        """手动推送 today.md 报告（校验失败时打印错误并返回 False）。

        Returns:
            True 表示推送成功，False 表示报告未就绪。
        """
        result = self.store.today_report()
        if not result.ready:
            logger.error(f"today.md 尚未就绪，无法推送：{result.text}")
            print(f"错误：{result.text}", file=sys.stderr)
            return False
        logger.info(f"开始手动推送今日安全情报，目标群: {len(self.allowed_chats)} 个")
        for chat_id in self.allowed_chats:
            for chunk in split_message(result.text):
                await self.client.send_message(chat_id, {
                    "msgtype": "markdown",
                    "markdown": {"content": chunk},
                })
            logger.info(f"已推送今日情报到群 {chat_id}")
        return True

    async def push_archive(self, date_str: str) -> bool:
        """手动推送指定日期的归档报告。

        Args:
            date_str: YYYY-MM-DD 格式的日期字符串。

        Returns:
            True 表示推送成功，False 表示报告未就绪。
        """
        result = self.store.get_archive_report(date_str)
        if not result.ready:
            logger.error(f"归档报告未就绪：{result.text}")
            print(f"错误：{result.text}", file=sys.stderr)
            return False
        logger.info(f"开始手动推送归档报告 {date_str}，目标群: {len(self.allowed_chats)} 个")
        for chat_id in self.allowed_chats:
            for chunk in split_message(result.text):
                await self.client.send_message(chat_id, {
                    "msgtype": "markdown",
                    "markdown": {"content": chunk},
                })
            logger.info(f"已推送归档报告 {date_str} 到群 {chat_id}")
        return True

    async def start(self) -> None:
        self.client.on("message.text", self.handle_text)
        self.client.on("authenticated", lambda: logger.info("企业微信智能机器人认证成功"))
        self.client.on("error", lambda error: logger.error(f"企业微信智能机器人错误：{error}"))

        schedule.every().day.at(self.daily_push_time).do(
            lambda: asyncio.create_task(self.push_daily())
        )

        logger.info(f"正在连接企业微信，每日推送时间: {self.daily_push_time}")
        logger.info(f"LLM: {'已启用' if self.llm_router else '未启用'} | "
                    f"联网搜索: {'已启用' if self.web_search else '未启用'}")
        await self.client.connect()

        # 主循环：等待关闭信号
        try:
            while getattr(self.client, "is_connected", True) and not self._shutdown_event.is_set():
                schedule.run_pending()
                # 使用短超时等待，以便及时响应关闭信号
                try:
                    await asyncio.wait_for(self._shutdown_event.wait(), timeout=1.0)
                    break  # 收到关闭信号，退出循环
                except asyncio.TimeoutError:
                    pass  # 超时继续循环
        finally:
            # 确保连接正常关闭
            await self.shutdown()

    async def shutdown(self) -> None:
        """优雅关闭 WebSocket 连接。"""
        if getattr(self.client, "is_connected", False):
            logger.info("正在关闭企业微信智能机器人连接...")
            try:
                # disconnect 是同步方法，不需要 await
                self.client.disconnect()
                # 等待一小段时间确保连接完全关闭
                await asyncio.sleep(0.5)
                logger.info("连接已关闭")
            except Exception as e:
                logger.error(f"关闭连接时出错：{e}")


def load_runner(config_path: Path) -> WeComAIBotRunner:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    root = config_path.parent
    bot_conf = config.get("wecom_ai_bot", {})

    bot_id_env = bot_conf.get("bot_id_env", "WECOM_BOT_ID")
    secret_env = bot_conf.get("secret_env", "WECOM_BOT_SECRET")
    bot_id = os.getenv(bot_id_env) or bot_conf.get("bot_id", "")
    secret = os.getenv(secret_env) or bot_conf.get("secret", "")
    if not bot_id or not secret:
        raise RuntimeError(f"请设置环境变量 {bot_id_env} 和 {secret_env}")

    logger.info(f"正在加载配置: {config_path}")
    logger.info(f"Bot ID: {bot_id[:8]}... | 配置文件: {config_path.name}")

    client = WSClient(
        bot_id=bot_id,
        secret=secret,
        max_reconnect_attempts=bot_conf.get("max_reconnect_attempts", -1),
    )
    return WeComAIBotRunner(
        client=client,
        store=ReportStore(root, config=str(config_path)),
        allowed_chats=set(bot_conf.get("allowed_chats", [])),
        daily_push_time=bot_conf.get("daily_push_time", "10:00"),
        llm_router=LLMCommandRouter.from_config(config),
        web_search=TavilyWebSearch.from_config(config),
    )


def setup_logging(log_file: str | None = None, level: str = "INFO") -> None:
    """配置日志：同时输出到控制台和文件（可选）。"""
    log_level = getattr(logging, level.upper(), logging.INFO)
    fmt = logging.Formatter(
        "%(asctime)s [%(name)s] %(levelname)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    root_logger = logging.getLogger("wecom_ai_bot")
    root_logger.setLevel(log_level)

    # 控制台输出
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(fmt)
    root_logger.addHandler(console_handler)

    # 文件输出（可选）
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(fmt)
        root_logger.addHandler(file_handler)
        root_logger.info(f"日志文件: {log_file}")


async def async_main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config.json")
    parser.add_argument("--log", help="日志文件路径（同时输出到控制台和文件）")
    parser.add_argument("--log-level", default="INFO",
                        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
                        help="日志级别 (默认: INFO)")
    parser.add_argument("--push-today", action="store_true",
                        help="手动推送今日报告（today.md），验证通过后推送并退出")
    parser.add_argument("--push-date", metavar="YYYY-MM-DD",
                        help="手动推送指定日期的归档报告，验证通过后推送并退出")
    args = parser.parse_args()

    setup_logging(log_file=args.log, level=args.log_level)

    # --- 手动推送模式 ---
    if args.push_date or args.push_today:
        if args.push_date and args.push_today:
            logger.error("--push-today 和 --push-date 不能同时使用。")
            sys.exit(2)

        logger.info("=" * 50)
        logger.info("手动推送模式启动")
        logger.info("=" * 50)

        runner = load_runner(Path(args.config).expanduser().absolute())
        try:
            await runner.client.connect()
        except Exception as e:
            logger.error(f"WebSocket 连接失败：{e}")
            sys.exit(1)

        success = False
        try:
            if args.push_date:
                success = await runner.push_archive(args.push_date)
            else:
                success = await runner.push_today_manual()
        finally:
            await runner.shutdown()

        sys.exit(0 if success else 1)

    # --- 正常长驻 Bot 模式 ---
    logger.info("=" * 50)
    logger.info("企业微信 AI 机器人启动")
    logger.info("=" * 50)

    runner = load_runner(Path(args.config).expanduser().absolute())

    # 注册信号处理器
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, runner._shutdown_event.set)

    try:
        await runner.start()
    except Exception as e:
        logger.error(f"机器人运行异常: {e}", exc_info=True)
        raise
    finally:
        logger.info("企业微信 AI 机器人已退出")


def main() -> None:
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
