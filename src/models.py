"""
数据模型 — NewsItem 新闻条目
"""

import hashlib
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Optional


CATEGORY_AI = "AI"
CATEGORY_TECH = "TECH"
CATEGORY_FINANCE = "FINANCE"
CATEGORY_VIDEO = "VIDEO"

ALL_CATEGORIES = [CATEGORY_AI, CATEGORY_TECH, CATEGORY_FINANCE, CATEGORY_VIDEO]

CATEGORY_LABELS = {
    CATEGORY_AI: "🤖 AI 资讯",
    CATEGORY_TECH: "🔧 科技动态",
    CATEGORY_FINANCE: "💰 财经要闻",
    CATEGORY_VIDEO: "▶ 热门视频",
}

CATEGORY_COLORS = {
    CATEGORY_AI: "#7c3aed",
    CATEGORY_TECH: "#0891b2",
    CATEGORY_FINANCE: "#059669",
    CATEGORY_VIDEO: "#e11d48",
}


@dataclass
class NewsItem:
    """统一新闻条目"""

    title: str
    summary: str
    url: str
    source_name: str
    source_icon: str
    source_color: str
    category: str
    published_at: str  # ISO格式时间字符串
    fetched_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    thumbnail_url: str = ""
    id: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = hashlib.sha256(self.url.encode("utf-8")).hexdigest()[:16]

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "NewsItem":
        return cls(**data)

    @classmethod
    def from_rss_entry(cls, entry: dict, source: dict, category: str) -> Optional["NewsItem"]:
        """从 RSS entry 创建 NewsItem"""
        title = str(entry.get("title", "")).strip()
        link = str(entry.get("link", "")).strip()
        if not title or not link:
            return None

        # 摘要
        summary = ""
        is_video = category == "VIDEO"
        if is_video and entry.get("author"):
            summary = str(entry.get("author", ""))
        else:
            for key in ("summary", "description", "subtitle"):
                val = entry.get(key)
                if val:
                    summary = _strip_html(str(val))
                    break
        summary = summary[:200] if summary else ""

        # 发布时间
        published = entry.get("published_parsed") or entry.get("updated_parsed")
        pub_str = ""
        if published:
            try:
                from time import mktime
                dt = datetime.fromtimestamp(mktime(published), tz=timezone.utc)
                pub_str = dt.isoformat()
            except Exception:
                pub_str = str(entry.get("published", ""))

        # 缩略图
        thumbnail = ""
        media_content = entry.get("media_content", [])
        if media_content:
            for media in media_content:
                if str(media.get("type", "")).startswith("image"):
                    thumbnail = str(media.get("url", ""))
                    break
        if not thumbnail and "links" in entry:
            for link_item in entry["links"]:
                if str(link_item.get("rel", "")) == "enclosure" and str(link_item.get("type", "")).startswith("image"):
                    thumbnail = str(link_item.get("href", ""))
                    break

        return cls(
            title=title,
            summary=summary,
            url=link,
            source_name=source.get("name", ""),
            source_icon=source.get("icon", ""),
            source_color=source.get("color", "#666"),
            category=category,
            published_at=pub_str,
            thumbnail_url=thumbnail,
        )


def _strip_html(text: str) -> str:
    """去除 HTML 标签"""
    import re
    clean = re.sub(r"<[^>]+>", "", text)
    clean = re.sub(r"\s+", " ", clean).strip()
    return clean