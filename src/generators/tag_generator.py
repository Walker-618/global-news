"""
标签页生成器 — 生成单个分类的独立列表页（分页 + 静态路径）
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
        if minutes < 1: return "刚刚"
        if minutes < 60: return f"{minutes}分钟前"
        hours = int(minutes / 60)
        if hours < 24: return f"{hours}小时前"
        days = int(hours / 24)
        if days < 7: return f"{days}天前"
        return pub.strftime("%m月%d日")
    except:
        return iso_str[:10]


def _date_context() -> dict:
    from datetime import datetime
    now = datetime.now()
    week_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
    ctx = {"date_str": f"{now.year}年{now.month}月{now.day}日", "week_str": week_names[now.weekday()], "lunar_str": ""}
    try:
        from lunarcalendar import Converter, Solar
        lunar = Converter.Solar2Lunar(Solar(now.year, now.month, now.day))
        ctx["lunar_str"] = f"{lunar.month}月{lunar.day}日"
    except:
        pass
    return ctx


def generate_tag_pages():
    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
    template = env.get_template("tag-page.html.j2")
    date_ctx = _date_context()

    for cat in ALL_CATEGORIES:
        items = load_items(cat, 200)
        if not items:
            continue
        total_pages = math.ceil(len(items) / PAGE_SIZE)
        label = CATEGORY_LABELS[cat]
        color = CATEGORY_COLORS[cat]
        key = cat.lower()

        for page in range(1, total_pages + 1):
            start = (page - 1) * PAGE_SIZE
            page_items = items[start:start + PAGE_SIZE]
            rendered = [{
                "title": it.title, "summary": it.summary, "url": it.url,
                "thumbnail_url": it.thumbnail_url, "source_name": it.source_name,
                "source_icon": it.source_icon, "source_color": it.source_color,
                "time_ago": _time_ago(it.published_at),
            } for it in page_items]

            html = template.render(**date_ctx,
                tag_label=label, tag_key=key, tag_color=color,
                items=rendered, total=len(items),
                page=page, total_pages=total_pages,
                back_url="../../index.html",
                page_url=f"./{page}.html" if page > 1 else "./index.html",
            )

            page_dir = os.path.join(OUTPUT_DIR, "tag-page", key)
            os.makedirs(page_dir, exist_ok=True)
            fname = f"{page}.html" if page > 1 else "index.html"
            with open(os.path.join(page_dir, fname), "w", encoding="utf-8") as f:
                f.write(html)

        logger.info(f"✅ [{cat}] {len(items)}条 × {total_pages}页 → tag-page/{key}/")

    return os.path.join(OUTPUT_DIR, "tag-page")