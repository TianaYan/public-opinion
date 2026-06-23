"""
B 站爬虫 —— 走 bilibili.com 公开搜索 + 公开评论接口
WBI 签名用简化版(mixin_table 在 2024-02 后已弃用,B 站现在主要靠 cookie 限速)
"""
import time
import re
import json
from typing import List, Dict
from .base import safe_get, rate_limit, random_ua
from config import config


@rate_limit(seconds=config.BILIBILI_INTERVAL)
def search_bilibili(keyword: str, max_count: int = None) -> List[Dict]:
    """
    搜索 B 站视频,返回标准化视频列表(只取元信息,不抓评论)
    """
    max_count = max_count or config.MAX_POSTS_PER_KEYWORD
    results = []
    page = 1
    headers = {
        "User-Agent": random_ua(),
        "Referer": "https://www.bilibili.com",
    }
    while len(results) < max_count and page <= 3:
        url = "https://api.bilibili.com/x/web-interface/search/all/v2"
        params = {
            "keyword": keyword,
            "page": page,
            "page_size": 20,
        }
        resp = safe_get(url, params=params, headers=headers, timeout=15)
        if not resp:
            break
        try:
            data = resp.json()
        except Exception:
            break
        if data.get("code") != 0:
            break
        items = data.get("data", {}).get("result", [])
        for cat in items:
            if cat.get("result_type") != "video":
                continue
            for v in cat.get("data", []):
                aid = v.get("aid")
                if not aid:
                    continue
                results.append({
                    "platform": "bilibili",
                    "post_id": f"video_{aid}",
                    "title": re.sub(r"<[^>]+>", "", v.get("title", "")),
                    "content": v.get("description", "")[:300],
                    "author": v.get("author", ""),
                    "url": f"https://www.bilibili.com/video/av{aid}",
                    "publish_time": "",
                    "likes": v.get("like", 0) or 0,
                    "comments": v.get("reply", 0) or 0,
                    "extra": {"aid": aid, "bvid": v.get("bvid", "")},
                })
                if len(results) >= max_count:
                    break
            if len(results) >= max_count:
                break
        page += 1
        time.sleep(2)
    return results


@rate_limit(seconds=config.BILIBILI_INTERVAL)
def fetch_video_comments(aid: int, max_count: int = None) -> List[Dict]:
    """抓单个视频的评论"""
    max_count = max_count or config.MAX_BILIBILI_COMMENTS
    results = []
    headers = {
        "User-Agent": random_ua(),
        "Referer": f"https://www.bilibili.com/video/av{aid}",
    }
    page = 1
    while len(results) < max_count and page <= 50:
        url = "https://api.bilibili.com/x/v2/reply"
        params = {
            "type": 1,  # 1=视频
            "oid": aid,
            "pn": page,
            "ps": 20,
            "sort": 2,  # 按热度
        }
        resp = safe_get(url, params=params, headers=headers, timeout=15)
        if not resp:
            break
        try:
            data = resp.json()
        except Exception:
            break
        if data.get("code") != 0:
            break
        replies = data.get("data", {}).get("replies", []) or []
        if not replies:
            break
        for r in replies:
            content = (r.get("content", {}) or {}).get("message", "")
            member = r.get("member", {}) or {}
            rpid = r.get("rpid")
            if not rpid or not content:
                continue
            results.append({
                "platform": "bilibili_comment",
                "post_id": f"comment_{aid}_{rpid}",
                "title": "",
                "content": content[:500],
                "author": member.get("uname", ""),
                "url": f"https://www.bilibili.com/video/av{aid}#reply{rpid}",
                "publish_time": "",
                "likes": r.get("like", 0) or 0,
                "comments": r.get("rcount", 0) or 0,
                "extra": {"aid": aid},
            })
            if len(results) >= max_count:
                break
        page += 1
        time.sleep(2)
    return results


def search_and_fetch_comments(keyword: str, max_videos: int = 5,
                               max_comments_per_video: int = 100) -> List[Dict]:
    """组合:搜视频 + 抓每条视频的评论"""
    videos = search_bilibili(keyword, max_count=max_videos)
    all_items = videos[:]
    for v in videos:
        extra = v.get("extra", {})
        aid = extra.get("aid")
        if not aid:
            continue
        try:
            comments = fetch_video_comments(aid, max_count=max_comments_per_video)
            all_items.extend(comments)
        except Exception as e:
            print(f"[bilibili] 抓视频 av{aid} 评论失败: {e}")
    return all_items
