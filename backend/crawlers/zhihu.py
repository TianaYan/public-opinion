"""
知乎爬虫 —— 走 www.zhihu.com 公开搜索 API
"""
import time
import re
import json
from typing import List, Dict
from .base import safe_get, rate_limit
from config import config


@rate_limit(seconds=config.ZHIHU_INTERVAL)
def search_zhihu(keyword: str, max_count: int = None) -> List[Dict]:
    """
    搜索知乎,返回标准化帖子列表
    接口:https://www.zhihu.com/api/v4/search_v3
    """
    max_count = max_count or config.MAX_POSTS_PER_KEYWORD
    results = []
    offset = 0
    limit = 10
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://www.zhihu.com/search",
        "x-api-version": "3.0.91",
        "x-app-za": "OS=Web&Browser=Chrome120&Version=120.0.0.0&Timestamp=" + str(int(time.time())),
    }

    while len(results) < max_count and offset < 50:  # 最多 50 条
        url = "https://www.zhihu.com/api/v4/search_v3"
        params = {
            "t": "general",
            "q": keyword,
            "correction": 1,
            "offset": offset,
            "limit": limit,
            "show_all_topics": 0,
            "search_hash_id": "",
            "vertical_info": [],
            "search_source": "normal",
        }
        resp = safe_get(url, params=params, headers=headers, timeout=15)
        if not resp:
            break
        try:
            data = resp.json()
        except Exception:
            break

        # 新版 API 直接返回 data 数组
        items = data.get("data", [])
        if not isinstance(items, list):
            break

        for item in items:
            if item.get("type") not in ("search_result", "answer", "article"):
                continue
            obj = item.get("object", {}) or {}
            obj_type = obj.get("type", "")
            if obj_type == "answer":
                question = obj.get("question", {}) or {}
                title = question.get("title", "")
                content = obj.get("content", "") or obj.get("excerpt", "")
                post_id = str(obj.get("id", ""))
                author = (obj.get("author", {}) or {}).get("name", "")
                url_post = f"https://www.zhihu.com/question/{question.get('id')}/answer/{obj.get('id')}"
            elif obj_type == "article":
                title = obj.get("title", "")
                content = obj.get("content", "") or obj.get("excerpt", "")
                post_id = str(obj.get("id", ""))
                author = (obj.get("author", {}) or {}).get("name", "")
                url_post = f"https://zhuanlan.zhihu.com/p/{obj.get('id')}"
            else:
                # 兜底
                title = obj.get("title", "") or obj.get("excerpt_new", "")[:50]
                content = obj.get("content", "") or obj.get("excerpt", "")
                post_id = str(obj.get("id", ""))
                author = (obj.get("author", {}) or {}).get("name", "")
                url_post = obj.get("url", "")

            content = re.sub(r"<[^>]+>", "", content)[:500]
            results.append({
                "platform": "zhihu",
                "post_id": post_id,
                "title": title,
                "content": content,
                "author": author,
                "url": url_post,
                "publish_time": "",
                "likes": obj.get("voteup_count", 0) or 0,
                "comments": obj.get("comment_count", 0) or 0,
            })
            if len(results) >= max_count:
                break
        offset += limit
        time.sleep(2)
    return results
