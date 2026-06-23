"""
基础模块 —— 通用 HTTP 头、限速装饰器、UA 池
"""
import random
import time
import functools
from typing import Optional
import requests

UA_POOL = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]


def random_ua() -> str:
    return random.choice(UA_POOL)


def get_proxies() -> Optional[dict]:
    """如果配了 HTTP_PROXY,返回代理字典"""
    from config import config
    if config.HTTP_PROXY:
        return {"http": config.HTTP_PROXY, "https": config.HTTP_PROXY}
    return None


def safe_get(url: str, params: Optional[dict] = None, headers: Optional[dict] = None,
             timeout: int = 15, max_retry: int = 3) -> Optional[requests.Response]:
    """带重试的 GET"""
    if headers is None:
        headers = {}
    headers.setdefault("User-Agent", random_ua())
    headers.setdefault("Accept-Language", "zh-CN,zh;q=0.9")

    proxies = get_proxies()
    last_err = None
    last_status = None
    for i in range(max_retry):
        try:
            resp = requests.get(
                url, params=params, headers=headers,
                timeout=timeout, proxies=proxies, allow_redirects=True,
            )
            last_status = resp.status_code
            if resp.status_code == 200:
                return resp
            elif resp.status_code in (429, 403):
                # 被限流,长 sleep 再试
                wait = (i + 1) * 10 + random.randint(5, 15)
                print(f"[safe_get] 被限流 {resp.status_code} ({url[:60]}...),等待 {wait}s")
                time.sleep(wait)
            else:
                print(f"[safe_get] 非 200 状态 {resp.status_code} ({url[:60]}...)")
                time.sleep(2)
        except Exception as e:
            last_err = e
            print(f"[safe_get] 异常 {type(e).__name__}: {e} ({url[:60]}...)")
            time.sleep((i + 1) * 3)
    if last_err:
        print(f"[safe_get] 最终失败: {url} -> {last_err}")
    elif last_status:
        print(f"[safe_get] 最终失败: {url} -> status={last_status}")
    else:
        print(f"[safe_get] 最终失败: {url} -> 未知")
    return None


def rate_limit(seconds: float):
    """装饰器:函数调用之间至少间隔 seconds 秒"""
    last_call = {"t": 0.0}
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            now = time.time()
            wait = seconds - (now - last_call["t"])
            if wait > 0:
                time.sleep(wait + random.uniform(0.5, 2.0))
            result = func(*args, **kwargs)
            last_call["t"] = time.time()
            return result
        return wrapper
    return decorator
