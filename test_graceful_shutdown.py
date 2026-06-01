#!/usr/bin/env python3
"""测试优雅关闭功能。

用法：
1. 运行脚本：python3 test_graceful_shutdown.py
2. 等待连接成功（看到"企业微信智能机器人认证成功"）
3. 按 Ctrl+C
4. 应该看到"正在关闭企业微信智能机器人连接..."和"连接已关闭"
5. 立即再次运行脚本，应该能够立即连接成功（无需等待 5 分钟）
"""

import asyncio
import os
from pathlib import Path

from wecom_ai_bot import load_runner


async def main():
    config_path = Path("config.json").expanduser().absolute()
    runner = load_runner(config_path)

    print("启动机器人...")
    print("连接成功后按 Ctrl+C 测试优雅关闭")
    print("-" * 60)

    await runner.start()

    print("-" * 60)
    print("机器人已停止")


if __name__ == "__main__":
    asyncio.run(main())
