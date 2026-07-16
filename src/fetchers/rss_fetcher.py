"""
RSS 采集器 — 通用 RSS feed 抓取与解析
"""

import logging
from typing import List, Optional

import feedparser
import httpx

from src.models import NewsItem

logger = logging.getLogger(__name__)


def fetch_source(source: dict, proxy_config: Optional[dict] = None, timeout: int = 30) -> List[NewsItem]:
    """
    从单个 RSS 源采集新闻

    Args:
        source: 数据源配置 (name, icon, color, category, rss_url, needs_proxy)
        proxy_config: 代理配置 {http, https}
        timeout: 请求超时(秒)

    Returns:
        NewsItem 列表
    """
    url = source["rss_url"]
    needs_proxy = source.get("needs_proxy", False)
    category = source["category"]

    logger.info(f"正在采集 [{source['name']}] {url}")

    # 获取 RSS 内容
    raw_xml = _fetch_xml(url, proxy_config if needs_proxy else None, timeout)
    if raw_xml is None:
        logger.warning(f"采集失败 [{source['name']}] — 无法获取内容")
        return []

    # 解析 RSS
    feed = feedparser.parse(raw_xml)
    if feed.bozo and not feed.entries:
        logger.warning(f"解析失败 [{source['name']}] — {feed.bozo_exception}")
        return []

    # 转换为 NewsItem
    items = []
    for entry in feed.entries:
        item = NewsItem.from_rss_entry(entry, source, category)
        if item:
            items.append(item)

    logger.info(f"采集完成 [{source['name']}] — 获取 {len(items)} 条")
    return items


def _fetch_xml(url: str, proxy: Optional[dict] = None, timeout: int = 30) -> Optional[str]:
    """获取 RSS XML 内容"""
    try:
        client_kwargs = {
            "timeout": timeout,
            "follow_redirects": True,
            "headers": {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/125.0.0.0 Safari/537.36"
                )
            },
        }
        if proxy:
            client_kwargs["proxy"] = proxy.get("http") or proxy.get("https")
        with httpx.Client(**client_kwargs) as client:
            resp = client.get(url)
            resp.raise_for_status()
            return resp.text
    except httpx.TimeoutException:
        logger.error(f"请求超时: {url}")
        return None
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP错误 {e.response.status_code}: {url}")
        return None
    except Exception as e:
        logger.error(f"请求异常: {url} — {e}")
        return None