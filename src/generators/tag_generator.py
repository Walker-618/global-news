"""
标签页生成器 — 生成单个分类的独立列表页
"""

import logging
import os
import math

from jinja2 import Environment, FileSystemLoader

from src.storage import load_items
from src.models import CATEGORY_LABELS, CATEGORY_COLORS, ALL_CATEGORIES

logger = logging.getLogger(__name__)

TEMPLATE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "templates")
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "dist")

PAGE_SIZE = 20


def _time_ago(iso_str: str) -> str:
    if not iso_str:
        return ""
    try:
        from datetime import datetime, timezone
        pub = datetime.fromisoformat(iso_str)
        now = datetime.now(timezone.utc)
        diff = now - pub
        minutes = int(diff.total_seconds() / 60)
        if minutes < 1:
            return "刚刚"
        if minutes < 60:
            return f"{minutes}分钟前"
        hours = int(minutes / 60)
        if hours < 24:
            return f"{hours}小时前"
        days = int(hours / 24)
        if days < 7:
            return f"{days}天前"
        return pub.strftime("%m月%d日")
    except Exception:
        return iso_str[:10]


def _date_context() -> dict:
    from datetime import datetime
    now = datetime.now()
    week_names = ["周日", "周一", "周二", "周三", "周四", "周五", "周六"]
    return {
        "date_str": f"{now.year}年{now.month}月{now.day}日",
        "week_str": week_names[now.weekday()],
        "lunar_str": "",
    }


def generate_tag_pages():
    """为所有分类生成标签列表页（分页）"""
    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
    template = env.get_template("tag-page.html.j2")
    ctx = _date_context()

    for cat in ALL_CATEGORIES:
        items = load_items(cat, 200)  # 最多加载200条
        if not items:
            logger.info(f"跳过 [{cat}] — 无数据")
            continue

        total_pages = math.ceil(len(items) / PAGE_SIZE)
        label = CATEGORY_LABELS[cat]
        color = CATEGORY_COLORS[cat]
        key = cat.lower()

        for page in range(1, total_pages + 1):
            start = (page - 1) * PAGE_SIZE
            end = start + PAGE_SIZE
            page_items = items[start:end]

            rendered_items = []
            for item in page_items:
                rendered_items.append({
                    "title": item.title,
                    "summary": item.summary,
                    "url": item.url,
                    "thumbnail_url": item.thumbnail_url,
                    "source_name": item.source_name,
                    "source_icon": item.source_icon,
                    "source_color": item.source_color,
                    "time_ago": _time_ago(item.published_at),
                })

            html = template.render(**ctx, **{
                "tag_label": label,
                "tag_key": key,
                "tag_color": color,
                "items": rendered_items,
                "total": len(items),
                "page": page,
                "total_pages": total_pages,
            })

            # 输出: tag-page/ai/1.html, tag-page/ai/2.html, ...
            page_dir = os.path.join(OUTPUT_DIR, "tag-page", key)
            os.makedirs(page_dir, exist_ok=True)
            fname = f"{page}.html" if page > 1 else "index.html"
            out_path = os.path.join(page_dir, fname)
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(html)

        logger.info(f"✅ [{cat}] {len(items)}条 × {total_pages}页 → tag-page/{key}/")

    return os.path.join(OUTPUT_DIR, "tag-page")