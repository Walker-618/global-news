"""
首页生成器 — 从 data/index.json 渲染 index.html
"""

import logging
import os
from datetime import datetime, timezone
from typing import List

from jinja2 import Environment, FileSystemLoader

from src.storage import get_index, load_items
from src.models import ALL_CATEGORIES, CATEGORY_LABELS, CATEGORY_COLORS

logger = logging.getLogger(__name__)

TEMPLATE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "templates")
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "dist")

GRADIENTS = [
    "linear-gradient(135deg,#0f172a,#1e3a5f)",
    "linear-gradient(135deg,#1e293b,#312e81)",
    "linear-gradient(135deg,#1e293b,#4f46e5)",
    "linear-gradient(135deg,#1e293b,#3730a3)",
    "linear-gradient(135deg,#1e293b,#0891b2)",
    "linear-gradient(135deg,#1e293b,#0e7490)",
    "linear-gradient(135deg,#1e293b,#059669)",
    "linear-gradient(135deg,#1e293b,#065f46)",
]

TAG_LABELS = {
    "AI": "🤖 AI",
    "TECH": "🔧 科技",
    "FINANCE": "💰 财经",
    "VIDEO": "▶ 视频",
}


def _time_ago(iso_str: str) -> str:
    """将 ISO 时间转为 'X小时前' 格式"""
    if not iso_str:
        return ""
    try:
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
    """生成日期上下文（含农历）"""
    from datetime import datetime
    now = datetime.now()
    week_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
    ctx = {
        "date_str": f"{now.year}年{now.month}月{now.day}日",
        "week_str": week_names[now.weekday()],
        "lunar_str": "",
    }
    try:
        from lunarcalendar import Converter, Solar, Lunar
        solar = Solar(now.year, now.month, now.day)
        lunar = Converter.Solar2Lunar(solar)
        ctx["lunar_str"] = f"{lunar.month}月{lunar.day}日"
    except Exception:
        ctx["lunar_str"] = ""
    return ctx


def generate_index():
    """生成首页 index.html"""
    index = get_index()
    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
    template = env.get_template("index.html.j2")

    # 准备精选卡片 (从各分类取前2条)
    featured = []
    for cat in ALL_CATEGORIES:
        items = load_items(cat, 2)
        for i, item in enumerate(items):
            featured.append({
                "title": item.title[:50],
                "url": item.url,
                "thumbnail_url": item.thumbnail_url,
                "source_name": item.source_name,
                "source_icon": item.source_icon,
                "source_color": item.source_color,
                "tag_label": TAG_LABELS.get(cat, cat),
                "gradient": GRADIENTS[len(featured) % len(GRADIENTS)],
                "time_ago": _time_ago(item.published_at),
            })

    # 准备标签内容
    tabs = []
    for cat in ALL_CATEGORIES:
        items = load_items(cat, 50)
        tab_items = []
        for item in items:
            tab_items.append({
                "title": item.title,
                "summary": item.summary,
                "url": item.url,
                "thumbnail_url": item.thumbnail_url,
                "source_name": item.source_name,
                "source_icon": item.source_icon,
                "source_color": item.source_color,
                "time_ago": _time_ago(item.published_at),
            })
        tabs.append({
            "key": cat.lower(),
            "label": CATEGORY_LABELS[cat],
            "count": len(tab_items),
            "color": CATEGORY_COLORS[cat],
            "articles": tab_items,
        })

    # 渲染
    ctx = _date_context()
    ctx.update({
        "featured": featured,
        "tabs": tabs,
    })

    html = template.render(**ctx)

    # 输出
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out_path = os.path.join(OUTPUT_DIR, "index.html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)

    logger.info(f"✅ 首页生成: {out_path} ({len(featured)}个精选, {sum(t['count'] for t in tabs)}条新闻)")
    return out_path