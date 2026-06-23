"""
微博爬虫 —— 走 m.weibo.cn 公开搜索接口(无需登录)
"""
import time
import re
from typing import List, Dict
from .base import safe_get, rate_limit
from config import config


@rate_limit(seconds=config.WEIBO_INTERVAL)
def search_weibo(keyword: str, max_count: int = None) -> List[Dict]:
    """
    搜索微博,返回标准化帖子列表
    接口:https://m.weibo.cn/api/container/getIndex
    """
    max_count = max_count or config.MAX_POSTS_PER_KEYWORD
    results = []
    page = 1
    import urllib.parse
    encoded_kw = urllib.parse.quote(keyword)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": f"https://m.weibo.cn/search?containerid=100103type%3D1%26q%3D{encoded_kw}",
        "Accept": "application/json, text/plain, */*",
    }
    containerid = f"100103type=1&q={encoded_kw}"

    while len(results) < max_count and page <= 5:  # 最多 5 页
        # 关键:中文关键词需要 URL 编码,requests 默认用 latin-1 编中文会炸
        # 用手动拼接 URL,绕过 requests 的自动编码
        import urllib.parse
        encoded_kw = urllib.parse.quote(keyword)
        url = f"https://m.weibo.cn/api/container/getIndex?containerid=100103type%3D1%26q%3D{encoded_kw}&page_type=searchall&page={page}"
        resp = safe_get(url, headers=headers, timeout=15)
        if not resp:
            break
        try:
            data = resp.json()
        except Exception:
            break

        if data.get("ok") != 1:
            break

        cards = data.get("data", {}).get("cards", [])
        for card in cards:
            if card.get("card_type") != 9:  # 9 = 微博
                continue
            mblog = card.get("mblog", {})
            post_id = mblog.get("id")
            if not post_id:
                continue
            text = re.sub(r"<[^>]+>", "", mblog.get("text", ""))
            user = mblog.get("user", {})
            results.append({
                "platform": "weibo",
                "post_id": str(post_id),
                "title": "",
                "content": text[:500],
                "author": user.get("screen_name", ""),
                "url": f"https://m.weibo.cn/detail/{post_id}",
                "publish_time": mblog.get("created_at", ""),
                "likes": mblog.get("attitudes_count", 0),
                "comments": mblog.get("comments_count", 0),
            })
            if len(results) >= max_count:
                break
        page += 1
        time.sleep(2)
    return results
