"""测试所有走百度的平台"""
import sys
sys.path.insert(0, '.')
from crawlers import baidu

print("\n=== 百度 site:weibo.com ===")
items = baidu.search_weibo_via_baidu("小鹏", max_count=3)
print(f"  结果: {len(items)} 条")
for it in items[:2]:
    print(f"    - {it.get('title', '')[:60]}")

print("\n=== 百度 site:zhihu.com ===")
items = baidu.search_zhihu_via_baidu("小鹏", max_count=3)
print(f"  结果: {len(items)} 条")
for it in items[:2]:
    print(f"    - {it.get('title', '')[:60]}")

print("\n=== 百度 site:xiaohongshu.com ===")
items = baidu.search_xhs_via_baidu("小鹏", max_count=3)
print(f"  结果: {len(items)} 条")
for it in items[:2]:
    print(f"    - {it.get('title', '')[:60]}")
