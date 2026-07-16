"""
DuckDuckGo 新闻采集器 — 搜索式获取最新新闻
"""
import logging, re
from typing import List, Optional
from datetime import datetime, timezone
from src.models import NewsItem

logger = logging.getLogger(__name__)

# 分类对应的搜索关键词
SEARCH_QUERIES = {
    "AI": [
        "artificial intelligence today", "AI technology news", "machine learning",
        "大模型 AI 新闻", "GPT AI 最新"
    ],
    "TECH": [
        "technology news today", "tech industry", "Silicon Valley",
        "科技新闻 最新", "智能手机 芯片"
    ],
    "FINANCE": [
        "financial markets today", "stock market news", "economy",
        "财经新闻 股市", "金融 投资 最新"
    ],
    "VIDEO": [
        "tech review YouTube", "technology review video", "AI explained"
    ],
}

SOURCE_MAP = {
    "AI": {"name": "DuckDuckGo AI", "icon": "D", "color": "#f97316"},
    "TECH": {"name": "DuckDuckGo Tech", "icon": "D", "color": "#0891b2"},
    "FINANCE": {"name": "DuckDuckGo Finance", "icon": "D", "color": "#059669"},
    "VIDEO": {"name": "DuckDuckGo Video", "icon": "D", "color": "#e11d48"},
}


def fetch_ddg_news(category: str, max_per_query: int = 5) -> List[NewsItem]:
    """通过 DuckDuckGo 搜索指定分类的最新新闻"""
    from ddgs import DDGS

    source = SOURCE_MAP.get(category, SOURCE_MAP["TECH"])
    queries = SEARCH_QUERIES.get(category, SEARCH_QUERIES["TECH"])
    all_items = []
    seen_urls = set()

    for query in queries:
        try:
            with DDGS() as ddgs:
                results = list(ddgs.news(query, max_results=max_per_query))
            for r in results:
                url = r.get("url", "").strip()
                if not url or url in seen_urls:
                    continue
                seen_urls.add(url)
                title = r.get("title", "").strip()
                if not title:
                    continue
                body = r.get("body", "")[:200]
                pub_raw = r.get("date", "")
                # 尝试解析日期
                pub_str = ""
                if pub_raw:
                    try:
                        dt = datetime.strptime(pub_raw[:10], "%Y-%m-%d")
                        pub_str = dt.replace(tzinfo=timezone.utc).isoformat()
                    except:
                        pub_str = pub_raw
                item = NewsItem(
                    title=title,
                    summary=body,
                    url=url,
                    source_name=source["name"],
                    source_icon=source["icon"],
                    source_color=source["color"],
                    category=category,
                    published_at=pub_str,
                )
                all_items.append(item)
        except Exception as e:
            logger.warning(f"DuckDuckGo search '{query}' failed: {e}")

    logger.info(f"DuckDuckGo [{category}]: {len(all_items)}条")
    return all_items