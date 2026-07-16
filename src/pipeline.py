"""
采集主调度器 — 遍历所有数据源 → 采集 → 去重存储
"""

import logging
import time
from typing import List

import yaml

from src.fetchers.rss_fetcher import fetch_source
from src.storage import save_items, get_stats

logger = logging.getLogger(__name__)

CONFIG_PATH = "config/sources.yaml"


def load_config() -> dict:
    """加载 sources.yaml 配置"""
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


MAX_ITEMS_PER_SOURCE = 5


def run_pipeline(only_domestic: bool = False) -> dict:
    """
    执行完整采集流水线

    Args:
        only_domestic: 仅采集国内源（无需代理）

    Returns:
        采集结果统计
    """
    cfg = load_config()
    sources = cfg["sources"]
    proxy = cfg.get("proxy")

    results = {
        "total_sources": len(sources),
        "succeeded": 0,
        "failed": 0,
        "total_items": 0,
        "new_items": 0,
        "details": [],
    }

    for source in sources:
        needs_proxy = source.get("needs_proxy", False)
        if only_domestic and needs_proxy:
            logger.info(f"跳过 [{source['name']}] (需代理，仅国内模式)")
            continue

        proxy_config = proxy if needs_proxy else None
        category = source["category"]

        try:
            items = fetch_source(source, proxy_config)
            # 限流：每个源最多取 N 条，保证内容多样性
            items = items[:MAX_ITEMS_PER_SOURCE]
            results["total_items"] += len(items)

            if items:
                new_count = save_items(category, items)
                results["new_items"] += new_count
                results["succeeded"] += 1
                results["details"].append({
                    "name": source["name"],
                    "status": "ok",
                    "fetched": len(items),
                    "new": new_count,
                })
                logger.info(f"✅ [{source['name']}] {len(items)}条 → 新增{new_count}条")
            else:
                results["failed"] += 1
                results["details"].append({
                    "name": source["name"],
                    "status": "empty",
                    "fetched": 0,
                    "new": 0,
                })
                logger.warning(f"⚠️ [{source['name']}] 未获取到内容")
        except Exception as e:
            results["failed"] += 1
            results["details"].append({
                "name": source["name"],
                "status": "error",
                "error": str(e),
                "fetched": 0,
                "new": 0,
            })
            logger.error(f"❌ [{source['name']}] 异常: {e}")

    # 最终统计
    stats = get_stats()
    results["storage"] = stats
    results["duration_seconds"] = 0  # 调用者填写
    logger.info(
        f"流水线完成: "
        f"成功{results['succeeded']}/{results['total_sources']}个源, "
        f"共{results['total_items']}条, "
        f"新增{results['new_items']}条, "
        f"累计{stats['total']}条"
    )
    return results