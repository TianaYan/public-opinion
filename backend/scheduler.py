"""
调度器 —— 定时抓取 + 情感分析
"""
import time
import traceback
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

import db
from analyzer import analyze_sentiment
from crawlers import weibo, zhihu, bilibili, baidu
from config import config


def _process_keyword(keyword_word: str, keyword_id: int, crawler_fn, platform_label: str):
    """通用抓取 + 情感分析流程"""
    try:
        print(f"[{datetime.now():%H:%M:%S}] 抓取 [{platform_label}] 关键词: {keyword_word}")
        items = crawler_fn(keyword_word)
        if not items:
            print(f"  → {platform_label} 无结果")
            db.log_crawl(keyword_word, platform_label, "empty", 0)
            return

        # 入库 + 情感分析
        analyzed = 0
        for item in items:
            item["keyword_id"] = keyword_id
            db.upsert_post(item)
            # 情感分析
            text = (item.get("title", "") + " " + item.get("content", "")).strip()
            if not item.get("sentiment") and text:
                sentiment, score = analyze_sentiment(text)
                db.update_sentiment(item["platform"], item["post_id"], sentiment, score, keyword_id=keyword_id)
                analyzed += 1
        db.log_crawl(keyword_word, platform_label, "success", len(items))
        print(f"  → {platform_label} 抓取 {len(items)} 条,分析 {analyzed} 条")
    except Exception as e:
        err = traceback.format_exc()
        print(f"  → {platform_label} 失败: {e}\n{err}")
        db.log_crawl(keyword_word, platform_label, "failed", 0, str(e)[:500])


def run_all_crawlers():
    """遍历所有关键词,跑所有启用的平台"""
    keywords = db.list_keywords(enabled_only=True)
    if not keywords:
        print("[scheduler] 暂无启用关键词")
        return

    for kw in keywords:
        word = kw["word"]
        kid = kw["id"]

        if config.ENABLE_WEIBO:
            _process_keyword(word, kid, weibo.search_weibo, "weibo")
        if config.ENABLE_ZHIHU:
            _process_keyword(word, kid, zhihu.search_zhihu, "zhihu")
        if config.ENABLE_BILIBILI:
            _process_keyword(word, kid, bilibili.search_and_fetch_comments, "bilibili")
        if config.ENABLE_BAIDU_XHS:
            _process_keyword(word, kid, baidu.search_xhs_via_baidu, "xhs_baidu")
        if config.ENABLE_BAIDU_DOUYIN:
            _process_keyword(word, kid, baidu.search_douyin_via_baidu, "douyin_baidu")
        if config.ENABLE_BAIDU_WEIBO:
            _process_keyword(word, kid, baidu.search_weibo_via_baidu, "weibo_baidu")
        if config.ENABLE_BAIDU_ZHIHU:
            _process_keyword(word, kid, baidu.search_zhihu_via_baidu, "zhihu_baidu")


# ==================== 调度器 ====================
scheduler = BackgroundScheduler(timezone="Asia/Shanghai")


def start_scheduler():
    """启动后台调度任务"""
    if scheduler.running:
        return
    scheduler.add_job(
        run_all_crawlers,
        trigger=IntervalTrigger(seconds=config.CRAWL_INTERVAL),
        id="crawl_all",
        max_instances=1,
        coalesce=True,
        next_run_time=datetime.now(),  # 启动时先跑一次
    )
    scheduler.start()
    print(f"[scheduler] 已启动,间隔 {config.CRAWL_INTERVAL} 秒")


def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown(wait=False)
