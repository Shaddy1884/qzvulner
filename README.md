# qzvulner

每日安全资讯聚合与分发系统。自动从 OPML 定义的 RSS 源抓取安全新闻，生成 Markdown 日报，并通过企业微信 AI 机器人提供交互式查询。

Fork 自 [VulnTotal-Team/yarb](https://github.com/VulnTotal-Team/yarb)，新增 LLM 驱动的联网搜索、自然语言命令路由、企业微信智能交互等能力。

## 功能特性

- **RSS 聚合** — 多线程并行抓取，支持本地和远程 OPML 文件，自动按域名去重
- **Markdown 日报** — 生成 `today.md` + `archive/<年份>/<日期>.md`，通过 GitHub Pages 直接浏览
- **企业微信 AI 机器人** — 群聊 + 私聊双模式，支持正则命令和 LLM 自然语言意图识别
- **LLM 联网搜索** — LLM 查询扩展 → 并行 Tavily 搜索 → 去重 → 相关性重排序 → 摘要生成
- **定时调度** — 内置 cron 模式，也可用 GitHub Actions 零成本运行
- **部署打包** — 一键生成可部署的 `.tar.gz` 包，包含完整归档历史

## 快速开始

```sh
git clone https://github.com/Shaddy1884/qzvulner.git
cd qzvulner

# 创建并激活虚拟环境
python3 -m venv .venv
source .venv/bin/activate

# 安装依赖
./install.sh

# 配置环境变量（按需）
export TAVILY_API_KEY=tvly-xxx
export LLM_API_KEY=sk-xxx
export LLM_BASE_URL=https://api.openai.com/v1
export LLM_MODEL=gpt-4o
export WECOM_BOT_ID=xxx
export WECOM_BOT_SECRET=xxx

# 执行一次日报抓取
python yarb.py

# 启动企业微信 AI 机器人（长驻进程）
python wecom_ai_bot.py
```

## 命令行参考

### `yarb.py` — 日报抓取

| 参数 | 说明 |
|---|---|
| _(无参数)_ | 执行一次，抓取昨日文章 |
| `--update` | 先刷新远程 OPML 文件，再抓取 |
| `--cron 11:00` | 每天本地时间 11:00 自动执行 |
| `--date 2026-05-28` | 补录指定日期的归档 |
| `--config path/to/config.json` | 使用自定义配置文件 |
| `--test` | 测试模式，使用合成数据验证流程 |

```sh
# 单次抓取
python3 yarb.py

# 定时任务
nohup python3 yarb.py --cron 11:00 > run.log 2>&1 &

# 补录历史
python3 yarb.py --date 2026-05-28
```

### `wecom_ai_bot.py` — 企业微信 AI 机器人

```sh
python3 wecom_ai_bot.py --config config.json
```

长驻进程，通过 WebSocket 连接企业微信。支持 SIGINT/SIGTERM 优雅关闭。

#### 后台运行

```sh
# 后台运行 + 日志输出到文件
nohup python3 wecom_ai_bot.py --config config.json --log bot.log > /dev/null 2>&1 &

# 调试模式（详细日志）
nohup python3 wecom_ai_bot.py --config config.json --log bot.log --log-level DEBUG > /dev/null 2>&1 &

# 查看实时日志
tail -f bot.log
```

#### 支持的命令

| 命令 | 说明 | 示例 |
|---|---|---|
| `今日安全情报` | 查看当天日报 | `今日安全情报` |
| `最近N天` | 查看最近 N 天归档 | `最近3天` |
| `关键词 X` | 在历史归档中搜索标题 | `关键词 RCE` |
| `联网搜索 X` | 调用 LLM + Tavily 搜索 | `联网搜索 TongWeb 安全漏洞` |
| `搜索/查找/查询 X` | 自然语言联网搜索 | `搜索 Spring RCE 漏洞` |
| `刷新今日` | 重新执行 `yarb.py` 并返回日报 | `刷新今日` |
| `帮助` | 显示命令列表 | `帮助` |
| `id` | 显示当前会话 ID | `id` |

群聊中需 `@机器人 命令`；私聊直接发送命令即可。未识别的文本会由 LLM 自动判断意图。

### `diagnose_tavily.py` — 搜索管线诊断

展示从查询扩展到最终报告的每个阶段，用于调试 LLM 聚合效果：

```sh
python3 diagnose_tavily.py "TongWeb安全漏洞"
python3 diagnose_tavily.py "CVE-2026" --search-depth advanced
python3 diagnose_tavily.py "Spring RCE" --report-max-items 8
```

诊断输出包含 5 个阶段：查询扩展对比、各查询原始结果、合并去重、LLM 重排序评分、LLM 聚合报告，以及各阶段耗时。

### `package.py` — 部署打包

```sh
python3 package.py --version 2026.06.01
# → dist/qzvulner-2026.06.01.tar.gz
```

打包内容包括所有运行时文件、配置、RSS 源和完整归档历史。

## 配置

所有配置集中在 `config.json`，密钥优先读取环境变量，回退到配置值。

```jsonc
{
  "proxy": {
    "url": "http://127.0.0.1:7890",
    "rss": false,            // RSS 抓取是否走代理
    "web_search": true       // Tavily 搜索是否走代理
  },

  "rss": {
    "CustomRSS": {
      "enabled": true,
      "filename": "CustomRSS.opml"              // 本地文件（相对 rss/）
    },
    "CyberSecurityRSS": {
      "enabled": true,
      "url": "https://raw.githubusercontent.com/zer0yu/CyberSecurityRSS/master/CyberSecurityRSS.opml",
      "filename": "CyberSecurityRSS.opml"       // 远程 OPML（需 --update 刷新）
    }
  },

  "wecom_ai_bot": {
    "enabled": true,
    "bot_id_env": "WECOM_BOT_ID",
    "secret_env": "WECOM_BOT_SECRET",
    "allowed_chats": [],                        // 群聊白名单（空 = 允许所有群 + 全部私聊）
    "daily_push_time": "08:00",
    "max_reconnect_attempts": -1                // -1 = 无限重连
  },

  "llm": {
    "enabled": true,
    "api_key_env": "LLM_API_KEY",
    "base_url_env": "LLM_BASE_URL",
    "model_env": "LLM_MODEL",
    "timeout": 90
  },

  "web_search": {
    "enabled": true,
    "api_key_env": "TAVILY_API_KEY",
    "max_results": 15,
    "search_depth": "basic",                    // basic | advanced
    "topic": "general",
    "include_answer": true,
    "report_max_items": 10
  },

  "keywords": {
    "exclude": ["奖励", "放送"]                 // 标题包含这些词的文章会被丢弃
  }
}
```

## 架构

```
┌──────────────────────────────────────────────────────────────┐
│                    yarb.py (Batch Pipeline)                   │
│                                                              │
│  init_rss()  ──→  parseThread() ×100  ──→  update_today()   │
│  (OPML加载)       (ThreadPoolExecutor)      (写MD + 归档)    │
└──────────────────────────────────────────────────────────────┘
          │                                        │
          │                    today.md ←──────────┘
          │                    archive/<year>/<date>.md
          │
┌──────────────────────────────────────────────────────────────┐
│               wecom_ai_bot.py (Interactive Bot)               │
│                                                              │
│  WebSocket ──→ handle_text() ──→ normalize_command()         │
│                      │                    │                  │
│                      ▼                    ▼                  │
│              report.handle_command()                         │
│               ┌──────┴──────┐                                │
│               ▼             ▼                                │
│         regex 命令     LLM 意图路由                           │
│        (ReportStore)   (LLMCommandRouter)                    │
│                             │                                │
│                             ▼                                │
│                    TavilyWebSearch                           │
│              扩展 → 并行搜索 → 去重                          │
│              → LLM 重排序 → LLM 摘要                         │
└──────────────────────────────────────────────────────────────┘
```

### 模块职责

| 模块 | 职责 |
|---|---|
| `yarb.py` | 日报抓取主流程：RSS 加载、多线程解析、Markdown 生成 |
| `wecom_ai_bot.py` | 企业微信 WebSocket 机器人，消息路由，群聊/私聊检测 |
| `report.py` | `ReportStore` 归档查询，`handle_command()` 命令分发 |
| `llm.py` | `LLMCommandRouter` — 意图路由、查询扩展、重排序、摘要生成 |
| `web_search.py` | `TavilyWebSearch` — 并行搜索、去重、格式化回退 |
| `diagnose_tavily.py` | 搜索管线 5 阶段诊断工具 |
| `package.py` | 部署打包 |
| `utils.py` | 共享工具：rich console、Pattern 辅助类 |

## GitHub Actions

项目通过 GitHub Actions 每日自动运行，无需服务器。

**触发时间：** 每天 UTC 02:00（北京时间 10:00）

**流程：** 安装依赖 → 执行 `yarb.py` → 提交 `today.md` + `archive/` → 清理 7 天前的运行记录

Fork 后即可使用。如需企业微信推送，需额外部署 `wecom_ai_bot.py` 长驻进程。

## 添加 RSS 订阅源

**方式一：** 编辑 `rss/CustomRSS.opml`，添加 feed 链接：

```xml
<?xml version="1.0" encoding="UTF-8"?>
<opml version="2.0">
<head><title>CustomRSS</title></head>
<body>
  <outline type="rss"
    xmlUrl="https://forum.butian.net/Rss"
    text="奇安信攻防社区"
    title="奇安信攻防社区"
    htmlUrl="https://forum.butian.net" />
</body>
</opml>
```

**方式二：** 在 `config.json` 的 `rss` 中添加远程 OPML 仓库：

```json
{
  "rss": {
    "CyberSecurityRSS": {
      "enabled": true,
      "url": "https://raw.githubusercontent.com/zer0yu/CyberSecurityRSS/master/CyberSecurityRSS.opml",
      "filename": "CyberSecurityRSS.opml"
    }
  }
}
```

远程源需要 `--update` 参数才会拉取。`init_rss()` 会自动按域名去重，避免重复抓取同一 feed。

**推荐订阅源：**

- [WeChat2RSS](https://wechat2rss.xlab.app/list/all.html) 

## 开发

```sh
# 运行测试
python3 -m unittest discover tests -v

# 测试日报生成（合成数据，不抓取真实 feed）
python3 yarb.py --test

# 诊断搜索管线
python3 diagnose_tavily.py "TongWeb安全漏洞"
```

## 依赖

| 包 | 用途 |
|---|---|
| `rich` | 终端格式化输出 |
| `requests` | HTTP 请求 |
| `feedparser` | RSS/Atom 解析 |
| `listparser` | OPML 文件解析 |
| `pyfiglet` | ASCII art 横幅 |
| `schedule` | 定时调度 |
| `wecom-aibot-sdk` | 企业微信 AI 机器人 WebSocket SDK |
| `tavily-python` | Tavily 联网搜索 API |

## 致谢

本项目基于 [VulnTotal-Team/yarb](https://github.com/VulnTotal-Team/yarb) 二次开发。感谢 VulnTotal 安全团队的开源贡献。

## 许可证

[GNU General Public License v3.0](./LICENSE)
