#!/usr/bin/python3

import os
import json
import time
import schedule
import pyfiglet
import argparse
import datetime
import listparser
import feedparser
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

from utils import *

import requests
requests.packages.urllib3.disable_warnings()

# 北京时间 UTC+8 — 中文安全资讯聚合器统一使用北京时间判断"今天"
_BEIJING_OFFSET = datetime.timedelta(hours=8)


def _beijing_now():
    """返回当前北京时间（不依赖系统时区）。"""
    return datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None) + _BEIJING_OFFSET


def _utc_struct_to_beijing_date(d):
    """将 feedparser 的 published_parsed（UTC）转为北京时间日期。"""
    utc_dt = datetime.datetime(*d[:6])
    beijing_dt = utc_dt + _BEIJING_OFFSET
    return beijing_dt.date()

def update_today(data: list=[], target_date: str=None):
    """更新today"""
    if target_date is None:
        target_date = (_beijing_now() - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    root_path = Path(__file__).absolute().parent
    data_path = root_path.joinpath('temp_data.json')
    today_path = root_path.joinpath('today.md')
    archive_path = root_path.joinpath(f'archive/{target_date.split("-")[0]}/{target_date}.md')

    if not data and data_path.exists():
        with open(data_path, 'r') as f1:
            data = json.load(f1)

    archive_path.parent.mkdir(parents=True, exist_ok=True)
    with open(today_path, 'w+') as f1, open(archive_path, 'w+') as f2:
        content = f'# 每日安全资讯（{target_date}）\n\n'
        article_count = 0
        for item in data:
            (feed, value), = item.items()
            if value:
                content += f'- {feed}\n'
                for title, url in value.items():
                    content += f'  - [{title}]({url})\n'
                    article_count += 1
        if article_count == 0:
            content += '> 今日暂无收录安全资讯，源站未更新。\n'
        f1.write(content)
        f2.write(content)


def update_rss(rss: dict, proxy_url=''):
    """更新订阅源文件"""
    proxy = {'http': proxy_url, 'https': proxy_url} if proxy_url else {'http': None, 'https': None}

    (key, value), = rss.items()
    rss_path = root_path.joinpath(f'rss/{value["filename"]}')

    result = None
    if url := value.get('url'):
        r = requests.get(value['url'], proxies=proxy)
        if r.status_code == 200:
            with open(rss_path, 'w+') as f:
                f.write(r.text)
            print(f'[+] 更新完成：{key}')
            result = {key: rss_path}
        elif rss_path.exists():
            print(f'[-] 更新失败，使用旧文件：{key}')
            result = {key: rss_path}
        else:
            print(f'[-] 更新失败，跳过：{key}')
    else:
        print(f'[+] 本地文件：{key}')

    return result


def parseThread(conf: dict, url: str, proxy_url='', target_date=None):
    """获取文章线程"""
    if target_date is None:
        target_date = (_beijing_now() - datetime.timedelta(days=1)).date()

    def filter(title: str):
        """过滤文章"""
        for i in conf['exclude']:
            if i in title:
                return False
        return True

    proxy = {'http': proxy_url, 'https': proxy_url} if proxy_url else {'http': None, 'https': None}
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.75 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'Accept-Language': 'zh-CN,zh;q=0.9',
    }

    title = ''
    result = {}
    try:
        r = requests.get(url, timeout=10, headers=headers, verify=False, proxies=proxy)
        r = feedparser.parse(r.content)
        title = r.feed.title
        for entry in r.entries:
            d = entry.get('published_parsed') or entry.get('updated_parsed')
            if d is None:
                continue
            pubday = _utc_struct_to_beijing_date(d)
            if pubday == target_date and filter(entry.title):
                item = {entry.title: entry.link}
                print(item)
                result |= item
        console.print(f'[+] {title}\t{url}\t{len(result.values())}/{len(r.entries)}', style='bold green')
    except Exception as e:
        console.print(f'[-] failed: {url}', style='bold red')
        print(e)
    return title, result


def init_rss(conf: dict, update: bool=False, proxy_url=''):
    """初始化订阅源"""
    rss_list = []
    enabled = [{k: v} for k, v in conf.items() if v['enabled']]
    for rss in enabled:
        if update:
            if rss := update_rss(rss, proxy_url):
                rss_list.append(rss)
        else:
            (key, value), = rss.items()
            rss_list.append({key: root_path.joinpath(f'rss/{value["filename"]}')})

    # 合并相同链接
    feeds = []
    for rss in rss_list:
        (_, value), = rss.items()
        try:
            rss = listparser.parse(open(value).read())
            for feed in rss.feeds:
                url = feed.url.strip().rstrip('/')
                short_url = url.split('://')[-1].split('www.')[-1]
                check = [feed for feed in feeds if short_url in feed]
                if not check:
                    feeds.append(url)
        except Exception as e:
            console.print(f'[-] 解析失败：{value}', style='bold red')
            print(e)

    console.print(f'[+] {len(feeds)} feeds', style='bold yellow')
    return feeds


def job(args):
    """定时任务"""
    # 解析目标日期：--date YYYY-MM-DD，默认昨天（北京时间）
    target_date = (_beijing_now() - datetime.timedelta(days=1)).date()
    target_date_str = target_date.strftime("%Y-%m-%d")
    if args.date:
        try:
            target_date = datetime.datetime.strptime(args.date, "%Y-%m-%d").date()
            target_date_str = args.date
        except ValueError:
            console.print(f'[-] 日期格式错误：{args.date}，应为 YYYY-MM-DD', style='bold red')
            return

    print(f'{pyfiglet.figlet_format("yarb")}\n{target_date_str}')

    global root_path
    root_path = Path(__file__).absolute().parent
    if args.config:
        config_path = Path(args.config).expanduser().absolute()
    else:
        config_path = root_path.joinpath('config.json')
    with open(config_path) as f:
        conf = json.load(f)

    proxy_rss = conf['proxy']['url'] if conf['proxy']['rss'] else ''
    feeds = init_rss(conf['rss'], args.update, proxy_rss)

    results = []
    if args.test:
        # 测试数据
        results.extend({f'test{i}': {Pattern.create(i*500): 'test'}} for i in range(1, 20))
    else:
        # 获取文章
        numb = 0
        tasks = []
        with ThreadPoolExecutor(100) as executor:
            tasks.extend(executor.submit(parseThread, conf['keywords'], url, proxy_rss, target_date) for url in feeds)
            for task in as_completed(tasks):
                title, result = task.result()
                if result:
                    numb += len(result.values())
                    results.append({title: result})
        console.print(f'[+] {len(results)} feeds, {numb} articles', style='bold yellow')

        # temp_path = root_path.joinpath('temp_data.json')
        # with open(temp_path, 'w+') as f:
        #     f.write(json.dumps(results, indent=4, ensure_ascii=False))
        #     console.print(f'[+] temp data: {temp_path}', style='bold yellow')

        # 更新today
        update_today(results, target_date_str)


def argument():
    parser = argparse.ArgumentParser()
    parser.add_argument('--update', help='Update RSS config file', action='store_true', required=False)
    parser.add_argument('--date', help='Target date in YYYY-MM-DD format (defaults to yesterday, used for backfilling missed archives)', type=str, required=False)
    parser.add_argument('--cron', help='Execute scheduled tasks every day (eg:"11:00")', type=str, required=False)
    parser.add_argument('--config', help='Use specified config file', type=str, required=False)
    parser.add_argument('--test', help='Test with synthetic data', action='store_true', required=False)
    return parser.parse_args()

def main():
    args = argument()
    if args.cron and args.date:
        print('错误：--cron 和 --date 不能同时使用。补录历史请使用 --date，定时任务请使用 --cron。')
        return
    if args.cron:
        schedule.every().day.at(args.cron).do(job, args)
        while True:
            schedule.run_pending()
            time.sleep(1)
    else:
        job(args)

if __name__ == '__main__':
    main()
