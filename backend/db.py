"""
数据库模块 —— SQLite 封装,负责建表、增删改查
"""
import sqlite3
import json
from contextlib import contextmanager
from datetime import datetime
from typing import List, Dict, Optional
from config import config


@contextmanager
def get_conn():
    """上下文管理器,自动 commit/close"""
    conn = sqlite3.connect(str(config.DB_PATH))
    conn.row_factory = sqlite3.Row
    # 关键:强制 UTF-8 编码,避免 Windows GBK 控制台乱码
    conn.text_factory = lambda b: b.decode("utf-8", errors="replace")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    """初始化表结构"""
    with get_conn() as conn:
        cur = conn.cursor()
        # 关键词表
        cur.execute("""
            CREATE TABLE IF NOT EXISTS keywords (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                word TEXT NOT NULL UNIQUE,
                enabled INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # 帖子表(全平台统一)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                platform TEXT NOT NULL,
                post_id TEXT NOT NULL,
                keyword_id INTEGER,
                title TEXT,
                content TEXT,
                author TEXT,
                url TEXT,
                publish_time TIMESTAMP,
                sentiment TEXT,
                sentiment_score REAL,
                likes INTEGER DEFAULT 0,
                comments INTEGER DEFAULT 0,
                fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(platform, post_id, keyword_id),
                FOREIGN KEY (keyword_id) REFERENCES keywords(id)
            )
        """)
        # 抓取日志
        cur.execute("""
            CREATE TABLE IF NOT EXISTS crawl_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                keyword TEXT,
                platform TEXT,
                status TEXT,
                fetched_count INTEGER DEFAULT 0,
                error_msg TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # 索引
        cur.execute("CREATE INDEX IF NOT EXISTS idx_posts_keyword ON posts(keyword_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_posts_platform ON posts(platform)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_posts_time ON posts(fetched_at)")


# ==================== 关键词 CRUD ====================
def add_keyword(word: str) -> int:
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT OR IGNORE INTO keywords (word) VALUES (?)",
            (word,)
        )
        cur.execute("SELECT id FROM keywords WHERE word = ?", (word,))
        return cur.fetchone()["id"]


def list_keywords(enabled_only=False) -> List[Dict]:
    with get_conn() as conn:
        cur = conn.cursor()
        if enabled_only:
            cur.execute("SELECT * FROM keywords WHERE enabled = 1 ORDER BY id DESC")
        else:
            cur.execute("SELECT * FROM keywords ORDER BY id DESC")
        return [dict(r) for r in cur.fetchall()]


def toggle_keyword(keyword_id: int, enabled: bool):
    with get_conn() as conn:
        conn.execute("UPDATE keywords SET enabled = ? WHERE id = ?", (int(enabled), keyword_id))


def delete_keyword(keyword_id: int):
    with get_conn() as conn:
        conn.execute("DELETE FROM keywords WHERE id = ?", (keyword_id,))


# ==================== 帖子 CRUD ====================
def upsert_post(post: Dict):
    """插入或忽略(UNIQUE 约束下,已存在的不覆盖 sentiment)"""
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT OR IGNORE INTO posts
            (platform, post_id, keyword_id, title, content, author, url,
             publish_time, sentiment, sentiment_score, likes, comments)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            post["platform"],
            post["post_id"],
            post.get("keyword_id"),
            post.get("title"),
            post.get("content"),
            post.get("author"),
            post.get("url"),
            post.get("publish_time"),
            post.get("sentiment"),
            post.get("sentiment_score"),
            post.get("likes", 0),
            post.get("comments", 0),
        ))


def update_sentiment(platform: str, post_id: str, sentiment: str, score: float, keyword_id: Optional[int] = None):
    """更新情感分析结果(同 URL 可能被多个关键词搜到,只更新最近一条)"""
    with get_conn() as conn:
        cur = conn.cursor()
        if keyword_id is not None:
            conn.execute(
                "UPDATE posts SET sentiment = ?, sentiment_score = ? WHERE platform = ? AND post_id = ? AND keyword_id = ?",
                (sentiment, score, platform, post_id, keyword_id)
            )
        else:
            # 兜底:更新该 post_id 最新的那条
            cur.execute(
                "SELECT id FROM posts WHERE platform = ? AND post_id = ? ORDER BY fetched_at DESC LIMIT 1",
                (platform, post_id)
            )
            row = cur.fetchone()
            if row:
                conn.execute(
                    "UPDATE posts SET sentiment = ?, sentiment_score = ? WHERE id = ?",
                    (sentiment, score, row["id"])
                )


def list_posts(
    platform: Optional[str] = None,
    keyword_id: Optional[int] = None,
    sentiment: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
) -> List[Dict]:
    with get_conn() as conn:
        cur = conn.cursor()
        sql = "SELECT p.*, k.word AS keyword FROM posts p LEFT JOIN keywords k ON p.keyword_id = k.id WHERE 1=1"
        params = []
        if platform:
            sql += " AND p.platform = ?"
            params.append(platform)
        if keyword_id:
            sql += " AND p.keyword_id = ?"
            params.append(keyword_id)
        if sentiment:
            sql += " AND p.sentiment = ?"
            params.append(sentiment)
        sql += " ORDER BY p.fetched_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        cur.execute(sql, params)
        return [dict(r) for r in cur.fetchall()]


def get_stats() -> Dict:
    """统计信息:总数 / 各平台数量 / 各情感数量 / 今日新增"""
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) AS c FROM posts")
        total = cur.fetchone()["c"]

        cur.execute("SELECT platform, COUNT(*) AS c FROM posts GROUP BY platform")
        by_platform = {r["platform"]: r["c"] for r in cur.fetchall()}

        cur.execute("SELECT sentiment, COUNT(*) AS c FROM posts WHERE sentiment IS NOT NULL GROUP BY sentiment")
        by_sentiment = {r["sentiment"]: r["c"] for r in cur.fetchall()}

        cur.execute("SELECT COUNT(*) AS c FROM posts WHERE DATE(fetched_at) = DATE('now', 'localtime')")
        today = cur.fetchone()["c"]

        cur.execute("SELECT COUNT(*) AS c FROM posts WHERE DATE(fetched_at) >= DATE('now', '-7 days', 'localtime')")
        week = cur.fetchone()["c"]

        return {
            "total": total,
            "today": today,
            "week": week,
            "by_platform": by_platform,
            "by_sentiment": by_sentiment,
        }


def get_trend(days: int = 7) -> List[Dict]:
    """近 N 天每日情感趋势"""
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(f"""
            SELECT DATE(fetched_at, 'localtime') AS day,
                   sentiment,
                   COUNT(*) AS c
            FROM posts
            WHERE fetched_at >= DATE('now', '-{days} days', 'localtime')
              AND sentiment IS NOT NULL
            GROUP BY day, sentiment
            ORDER BY day ASC
        """)
        return [dict(r) for r in cur.fetchall()]


# ==================== 日志 ====================
def log_crawl(keyword: str, platform: str, status: str, count: int = 0, err: str = ""):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO crawl_logs (keyword, platform, status, fetched_count, error_msg) VALUES (?, ?, ?, ?, ?)",
            (keyword, platform, status, count, err)
        )
