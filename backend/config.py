"""
配置模块 —— 加载 .env 环境变量,提供全局配置
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# 加载 .env(项目根目录)
ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")


class Config:
    # ==================== DeepSeek(情感分析) ====================
    DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
    DEEPSEEK_BASE_URL = "https://api.deepseek.com"
    DEEPSEEK_MODEL = "deepseek-chat"

    # ==================== 调度频率(秒) ====================
    CRAWL_INTERVAL = int(os.getenv("CRAWL_INTERVAL", "1800"))  # 默认 30 分钟
    WEIBO_INTERVAL = int(os.getenv("WEIBO_INTERVAL", "30"))
    ZHIHU_INTERVAL = int(os.getenv("ZHIHU_INTERVAL", "60"))
    BILIBILI_INTERVAL = int(os.getenv("BILIBILI_INTERVAL", "90"))
    BAIDU_INTERVAL = int(os.getenv("BAIDU_INTERVAL", "60"))

    # ==================== 抓取上限 ====================
    MAX_POSTS_PER_KEYWORD = int(os.getenv("MAX_POSTS_PER_KEYWORD", "50"))
    MAX_BILIBILI_COMMENTS = int(os.getenv("MAX_BILIBILI_COMMENTS", "500"))

    # ==================== 代理(可选) ====================
    HTTP_PROXY = os.getenv("HTTP_PROXY", "")

    # ==================== 路径 ====================
    DATA_DIR = ROOT_DIR / "data"
    DB_PATH = DATA_DIR / "opinion.db"
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    # ==================== 平台启用开关 ====================
    # 直接爬的平台(部分平台 API 已失效,默认关闭)
    ENABLE_WEIBO = os.getenv("ENABLE_WEIBO", "false").lower() == "true"  # 微博 API 已 432 拒绝
    ENABLE_ZHIHU = os.getenv("ENABLE_ZHIHU", "false").lower() == "true"  # 知乎需要 zse 签名
    ENABLE_BILIBILI = os.getenv("ENABLE_BILIBILI", "true").lower() == "true"  # B 站可用
    # 走百度的平台(小红书/抖音/微博/知乎)
    ENABLE_BAIDU_XHS = os.getenv("ENABLE_BAIDU_XHS", "true").lower() == "true"
    ENABLE_BAIDU_DOUYIN = os.getenv("ENABLE_BAIDU_DOUYIN", "true").lower() == "true"
    ENABLE_BAIDU_WEIBO = os.getenv("ENABLE_BAIDU_WEIBO", "true").lower() == "true"
    ENABLE_BAIDU_ZHIHU = os.getenv("ENABLE_BAIDU_ZHIHU", "true").lower() == "true"

    # ==================== 服务 ====================
    HOST = os.getenv("HOST", "127.0.0.1")
    PORT = int(os.getenv("PORT", "8000"))


config = Config()
