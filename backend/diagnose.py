"""快速诊断脚本:直接测每个爬虫能不能拿到数据"""
import sys
sys.path.insert(0, '.')

print("\n=== 1. 微博 (m.weibo.cn) ===")
from crawlers.weibo import search_weibo
items = search_weibo("小鹏", max_count=3)
print(f"  微博结果: {len(items)} 条")
for it in items[:2]:
    print(f"    - {it['author']}: {it['content'][:60]}")

print("\n=== 2. 知乎 (zhihu.com) ===")
from crawlers.zhihu import search_zhihu
items = search_zhihu("小鹏", max_count=3)
print(f"  知乎结果: {len(items)} 条")
for it in items[:2]:
    print(f"    - {it.get('title', '')[:50]}: {it.get('content', '')[:60]}")

print("\n=== 3. B 站 (bilibili.com) ===")
from crawlers.bilibili import search_bilibili
items = search_bilibili("小鹏", max_count=3)
print(f"  B 站结果: {len(items)} 条")
for it in items[:2]:
    print(f"    - {it.get('title', '')[:50]}")

print("\n=== 4. 百度 site:xiaohongshu.com ===")
from crawlers.baidu import search_xhs_via_baidu
items = search_xhs_via_baidu("小鹏", max_count=3)
print(f"  百度→小红书结果: {len(items)} 条")
for it in items[:2]:
    print(f"    - {it.get('title', '')[:50]}")

print("\n=== 5. 百度 site:douyin.com ===")
from crawlers.baidu import search_douyin_via_baidu
items = search_douyin_via_baidu("小鹏", max_count=3)
print(f"  百度→抖音结果: {len(items)} 条")
for it in items[:2]:
    print(f"    - {it.get('title', '')[:50]}")

print("\n=== 诊断完成 ===")
