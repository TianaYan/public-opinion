"""
FastAPI 入口 —— 提供 HTTP API
"""
import threading
from typing import Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import db
from scheduler import scheduler, start_scheduler, stop_scheduler, run_all_crawlers
from config import config
from crawlers import weibo, zhihu, bilibili, baidu
from analyzer import analyze_sentiment


app = FastAPI(title="舆情监控 API", version="1.0.0")

# 跨域(允许本地前端访问)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== 启动 ====================
@app.on_event("startup")
def on_startup():
    db.init_db()
    start_scheduler()
    print(f"\n{'='*60}")
    print(f"  舆情监控服务已启动")
    print(f"  监听: http://{config.HOST}:{config.PORT}")
    print(f"  数据: {config.DB_PATH}")
    print(f"{'='*60}\n")


@app.on_event("shutdown")
def on_shutdown():
    stop_scheduler()


# ==================== Pydantic 模型 ====================
class KeywordIn(BaseModel):
    word: str


class KeywordToggle(BaseModel):
    enabled: bool


# ==================== 关键词 API ====================
@app.get("/api/keywords")
def api_list_keywords():
    return {"items": db.list_keywords()}


@app.post("/api/keywords")
def api_add_keyword(data: KeywordIn):
    word = data.word.strip()
    if not word:
        raise HTTPException(400, "关键词不能为空")
    if len(word) > 50:
        raise HTTPException(400, "关键词过长")
    kid = db.add_keyword(word)
    return {"id": kid, "word": word}


@app.put("/api/keywords/{kid}/toggle")
def api_toggle_keyword(kid: int, data: KeywordToggle):
    db.toggle_keyword(kid, data.enabled)
    return {"ok": True}


@app.delete("/api/keywords/{kid}")
def api_delete_keyword(kid: int):
    db.delete_keyword(kid)
    return {"ok": True}


# ==================== 帖子 API ====================
@app.get("/api/posts")
def api_list_posts(
    platform: Optional[str] = None,
    keyword_id: Optional[int] = None,
    sentiment: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
):
    items = db.list_posts(platform, keyword_id, sentiment, limit, offset)
    return {"items": items, "total": len(items)}


@app.get("/api/stats")
def api_stats():
    return db.get_stats()


@app.get("/api/trend")
def api_trend(days: int = 7):
    return {"items": db.get_trend(days)}


# ==================== 手动触发 ====================
@app.post("/api/crawl/now")
def api_crawl_now():
    """立即跑一次所有爬虫(后台线程,不阻塞)"""
    threading.Thread(target=run_all_crawlers, daemon=True).start()
    return {"ok": True, "message": "已开始抓取,请稍后查看"}


@app.post("/api/crawl/keyword/{kid}")
def api_crawl_keyword(kid: int, platform: Optional[str] = None):
    """手动跑某个关键词的某个平台"""
    kws = [k for k in db.list_keywords() if k["id"] == kid]
    if not kws:
        raise HTTPException(404, "关键词不存在")
    word = kws[0]["word"]
    platforms = {
        "weibo": weibo.search_weibo,
        "zhihu": zhihu.search_zhihu,
        "bilibili": bilibili.search_and_fetch_comments,
        "xhs_baidu": baidu.search_xhs_via_baidu,
        "douyin_baidu": baidu.search_douyin_via_baidu,
    }
    if platform and platform not in platforms:
        raise HTTPException(400, f"不支持的平台: {platform}")
    selected = {platform: platforms[platform]} if platform else platforms

    def _run():
        for label, fn in selected.items():
            if not _is_enabled(label):
                continue
            from scheduler import _process_keyword
            _process_keyword(word, kid, fn, label)
    threading.Thread(target=_run, daemon=True).start()
    return {"ok": True}


def _is_enabled(label: str) -> bool:
    return {
        "weibo": config.ENABLE_WEIBO,
        "zhihu": config.ENABLE_ZHIHU,
        "bilibili": config.ENABLE_BILIBILI,
        "xhs_baidu": config.ENABLE_BAIDU_XHS,
        "douyin_baidu": config.ENABLE_BAIDU_DOUYIN,
    }.get(label, True)


# ==================== 日志 API ====================
@app.get("/api/health")
def api_health():
    return {
        "status": "ok",
        "scheduler_running": scheduler.running,
        "deepseek_configured": bool(config.DEEPSEEK_API_KEY),
        "platforms": {
            "weibo": config.ENABLE_WEIBO,
            "zhihu": config.ENABLE_ZHIHU,
            "bilibili": config.ENABLE_BILIBILI,
            "xhs_via_baidu": config.ENABLE_BAIDU_XHS,
            "douyin_via_baidu": config.ENABLE_BAIDU_DOUYIN,
            "weibo_via_baidu": config.ENABLE_BAIDU_WEIBO,
            "zhihu_via_baidu": config.ENABLE_BAIDU_ZHIHU,
        },
    }


if __name__ == "__main__":
    import os
    import uvicorn
    # 部署平台会注入 PORT 环境变量(必须用 0.0.0.0 让外部能访问)
    port = int(os.getenv("PORT", config.PORT))
    host = os.getenv("HOST", "0.0.0.0" if os.getenv("RENDER") or os.getenv("RAILWAY_ENVIRONMENT") else config.HOST)
    print(f"启动服务: http://{host}:{port}")
    uvicorn.run("main:app", host=host, port=port, reload=False)
