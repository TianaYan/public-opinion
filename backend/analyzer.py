"""
情感分析模块 —— 调 DeepSeek API
没用的话可以走规则兜底
"""
import re
import time
from typing import Optional
from config import config


def _rule_based_sentiment(text: str) -> tuple[str, float]:
    """
    规则兜底(当没配 DEEPSEEK_API_KEY 时用)
    返回 (sentiment, score)
    """
    if not text:
        return ("中性", 0.5)
    positive_words = ["好", "棒", "喜欢", "爱", "优秀", "完美", "惊喜", "满意", "推荐", "支持",
                      "开心", "快乐", "赞", "成功", "胜利", "突破", "创新", "领先"]
    negative_words = ["差", "烂", "讨厌", "失望", "垃圾", "坑", "骗", "黑", "丑", "失败",
                      "崩溃", "问题", "bug", "故障", "投诉", "退款", "维权", "曝光", "抵制", "恶心"]
    pos = sum(1 for w in positive_words if w in text)
    neg = sum(1 for w in negative_words if w in text)
    if pos > neg and pos > 0:
        return ("正面", min(0.6 + pos * 0.05, 0.9))
    elif neg > pos and neg > 0:
        return ("负面", min(0.6 + neg * 0.05, 0.9))
    return ("中性", 0.5)


def analyze_sentiment(text: str, use_fallback: bool = True) -> tuple[str, float]:
    """
    分析一段文本的情感
    返回 (sentiment, score)
    sentiment: 正面 / 负面 / 中性
    score: 0-1 置信度
    """
    if not text or not text.strip():
        return ("中性", 0.5)

    # 没配 key 走规则
    if not config.DEEPSEEK_API_KEY or use_fallback:
        return _rule_based_sentiment(text)

    # 调 DeepSeek
    try:
        from openai import OpenAI
        client = OpenAI(
            api_key=config.DEEPSEEK_API_KEY,
            base_url=config.DEEPSEEK_BASE_URL,
        )
        prompt = (
            "请判断以下文本的情感倾向(只回复以下三个词之一: 正面 / 负面 / 中性)\n"
            "评分标准:0.9-1.0 强烈,0.6-0.8 明显,0.3-0.5 中性\n"
            "回复格式:sentiment|score(竖线分隔)\n"
            "示例:正面|0.85\n\n"
            f"文本:{text[:500]}"
        )
        resp = client.chat.completions.create(
            model=config.DEEPSEEK_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=20,
            temperature=0.1,
        )
        content = resp.choices[0].message.content.strip()
        # 解析 sentiment|score
        if "|" in content:
            parts = content.split("|", 1)
            sentiment = parts[0].strip()
            try:
                score = float(parts[1].strip())
            except ValueError:
                score = 0.7
        else:
            sentiment = content
            score = 0.7
        if sentiment not in ("正面", "负面", "中性"):
            # 兜底匹配
            if "正" in sentiment:
                sentiment = "正面"
            elif "负" in sentiment:
                sentiment = "负面"
            else:
                sentiment = "中性"
        return (sentiment, max(0.0, min(1.0, score)))
    except Exception as e:
        print(f"[analyzer] DeepSeek 调用失败,降级到规则: {e}")
        return _rule_based_sentiment(text)


def analyze_batch(texts: list[str], delay: float = 0.1) -> list[tuple[str, float]]:
    """批量分析(避免 QPS 过高)"""
    results = []
    for t in texts:
        results.append(analyze_sentiment(t))
        time.sleep(delay)
    return results
