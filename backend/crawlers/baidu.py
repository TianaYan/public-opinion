"""
百度爬虫 —— 走 baidu.com 公开搜索结果页
用 site: 语法绕过小红书/抖音的反爬,直接吃百度的索引
"""
import re
import time
import urllib.parse
from typing import List, Dict
from bs4 import BeautifulSoup
from .base import safe_get, rate_limit
from config import config


def _parse_baidu_html(html: str) -> List[Dict]:
    """解析百度搜索结果 HTML,提取标准字段"""
    soup = BeautifulSoup(html, "html.parser")
    results = []
    # 百度新版的搜索结果容器
    for item in soup.select("div.result, div.c-container"):
        # 跳过广告
        if item.select_one("span.ec-tuiguang"):
            continue
        title_a = item.select_one("h3 a, h3.t a, h3 a.t")
        if not title_a:
            continue
        title = title_a.get_text(strip=True)
        baidu_url = title_a.get("href", "")

        # 摘要(可能多个选择器)
        abstract_el = item.select_one(".c-abstract, .content-right_8Zs40, span.content-right_8Zs40")
        if not abstract_el:
            abstract_el = item.select_one("div.c-span-last")
        abstract = abstract_el.get_text(strip=True) if abstract_el else ""

        # 来源 + 时间
        source = ""
        info_el = item.select_one(".c-color-gray, .c-source, .c-info")
        if info_el:
            source = info_el.get_text(strip=True)

        if not title:
            continue
        results.append({
            "title": re.sub(r"\s+", " ", title),
            "abstract": re.sub(r"\s+", " ", abstract)[:500],
            "baidu_url": baidu_url,
            "source_text": source,
        })
    return results


def _resolve_real_url(baidu_url: str) -> str:
    """百度的链接是加密的 redirect,需要 head 请求拿到真实 URL"""
    if not baidu_url or "baidu.com/link" not in baidu_url:
        return baidu_url
    try:
        resp = safe_get(baidu_url, timeout=8)
        if resp:
            return resp.url
    except Exception:
        pass
    return baidu_url


@rate_limit(seconds=config.BAIDU_INTERVAL)
def search_baidu_site(keyword: str, site: str, max_count: int = None) -> List[Dict]:
    """
    在指定 site 内搜索关键词
    site 形如: xiaohongshu.com / douyin.com / bilibili.com / weibo.com
    """
    max_count = max_count or config.MAX_POSTS_PER_KEYWORD
    query = f"site:{site} {keyword}"
    results = []
    page = 0

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "zh-CN,zh;q=0.9",
    }

    # 平台标签(前端显示用)
    platform_map = {
        "xiaohongshu.com": "xhs",
        "douyin.com": "douyin",
        "bilibili.com": "bilibili_baidu",
        "weibo.com": "weibo_baidu",
        "zhihu.com": "zhihu_baidu",
    }
    platform = platform_map.get(site, f"baidu_{site.replace('.', '_')}")

    while len(results) < max_count and page < 5:  # 最多 5 页
        url = "https://www.baidu.com/s"
        params = {
            "wd": query,
            "pn": page * 10,
            "rn": 10,
            "tn": "json",  # 试着用 json,如果不行回退 HTML
        }
        # 实际抓 HTML 解析(更稳)
        params["tn"] = ""
        resp = safe_get(url, params=params, headers=headers, timeout=15)
        if not resp:
            break
        items = _parse_baidu_html(resp.text)
        if not items:
            break

        for it in items:
            # 解析真实 URL
            real_url = _resolve_real_url(it["baidu_url"])
            # 提取域名信息
            parsed = urllib.parse.urlparse(real_url)
            host = parsed.netloc.lower()
            # 提取发布时间(从 abstract 或 source_text 抓日期)
            publish_time = _extract_time(it.get("source_text", "") + " " + it.get("abstract", ""))

            # post_id 用 URL 自身(确定、跨进程稳定),但要安全去掉特殊字符
            safe_url = re.sub(r"[^a-zA-Z0-9]", "_", real_url)[:200]
            results.append({
                "platform": platform,
                "post_id": safe_url,
                "title": it["title"],
                "content": it["abstract"] or it["title"],
                "author": "",
                "url": real_url,
                "publish_time": publish_time,
                "likes": 0,
                "comments": 0,
                "extra": {"site": site, "host": host},
            })
            if len(results) >= max_count:
                break
        page += 1
        time.sleep(2)
    return results


def _extract_time(text: str) -> str:
    """从文本里提取日期,如 '2026-06-15' / '3天前' / '昨天'"""
    if not text:
        return ""
    # 优先匹配 2024-01-01 / 2024.1.1 / 2024/1/1
    m = re.search(r"(\d{4})[-./年](\d{1,2})[-./月](\d{1,2})", text)
    if m:
        return f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
    # 相对时间(暂时不处理,留空)
    return ""


def search_xhs_via_baidu(keyword: str, max_count: int = None) -> List[Dict]:
    """小红书数据(走百度 site:)"""
    return search_baidu_site(keyword, "xiaohongshu.com", max_count=max_count)


def search_douyin_via_baidu(keyword: str, max_count: int = None) -> List[Dict]:
    """抖音数据(走百度 site:)"""
    return search_baidu_site(keyword, "douyin.com", max_count=max_count)


def search_weibo_via_baidu(keyword: str, max_count: int = None) -> List[Dict]:
    """微博数据(走百度 site:,m.weibo.cn API 已风控)"""
    return search_baidu_site(keyword, "weibo.com", max_count=max_count)


def search_zhihu_via_baidu(keyword: str, max_count: int = None) -> List[Dict]:
    """知乎数据(走百度 site:,官方 API 需要 zse 签名)"""
    return search_baidu_site(keyword, "zhihu.com", max_count=max_count)


def search_general_news(keyword: str) -> List[Dict]:
    """全网新闻搜索(走百度,无 site 限定)"""
    return search_baidu_site(keyword, "")


def search_general_news(keyword: str) -> List[Dict]:
    """全网新闻搜索(走百度,无 site 限定)"""
    return search_baidu_site(keyword, "")
