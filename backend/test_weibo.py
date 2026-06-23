"""快速验证微博"""
import sys
sys.path.insert(0, '.')
from crawlers.weibo import search_weibo
items = search_weibo("小鹏", max_count=3)
print(f"微博结果: {len(items)} 条")
for it in items[:2]:
    author = it.get("author", "")
    content = it.get("content", "")[:60]
    print(f"  - {author}: {content}")
