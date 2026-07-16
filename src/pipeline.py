"""
采集主调度器 — RSS + DuckDuckGo 搜索 → 去重存储
"""
import logging, yaml
from src.fetchers.rss_fetcher import fetch_source
from src.fetchers.ddg_fetcher import fetch_ddg_news
from src.storage import save_items, get_stats
from src.models import ALL_CATEGORIES

logger = logging.getLogger(__name__)
CONFIG_PATH = "config/sources.yaml"
MAX_ITEMS_PER_SOURCE = 10
DDG_ITEMS_PER_CATEGORY = 15

def load_config() -> dict:
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)

def run_pipeline(only_domestic: bool = False) -> dict:
    cfg = load_config()
    sources = cfg["sources"]
    proxy = cfg.get("proxy")
    results = {"total_sources": len(sources), "succeeded": 0, "failed": 0,
               "total_items": 0, "new_items": 0, "details": []}

    # Phase 1: RSS 采集
    for source in sources:
        if only_domestic and source.get("needs_proxy", False):
            continue
        try:
            items = fetch_source(source, proxy if source.get("needs_proxy") else None)[:MAX_ITEMS_PER_SOURCE]
            results["total_items"] += len(items)
            if items:
                n = save_items(source["category"], items)
                results["new_items"] += n; results["succeeded"] += 1
                results["details"].append({"name": source["name"], "status": "ok", "fetched": len(items), "new": n})
                logger.info(f"✅ [{source['name']}] {len(items)}条 → 新增{n}条")
            else:
                results["failed"] += 1
                results["details"].append({"name": source["name"], "status": "empty", "fetched": 0, "new": 0})
                logger.warning(f"⚠️ [{source['name']}] 空")
        except Exception as e:
            results["failed"] += 1
            results["details"].append({"name": source["name"], "status": "error", "error": str(e), "fetched": 0, "new": 0})
            logger.error(f"❌ [{source['name']}] {e}")

    # Phase 2: DuckDuckGo 搜索（补充新鲜内容）
    for cat in ALL_CATEGORIES:
        try:
            items = fetch_ddg_news(cat, max_per_query=5)[:DDG_ITEMS_PER_CATEGORY]
            if items:
                n = save_items(cat, items)
                results["total_items"] += len(items)
                results["new_items"] += n
                logger.info(f"✅ [DuckDuckGo {cat}] {len(items)}条 → 新增{n}条")
        except Exception as e:
            logger.error(f"❌ [DuckDuckGo {cat}] {e}")

    stats = get_stats()
    results["storage"] = stats
    logger.info(f"流水线完成: 成功{results['succeeded']}/{results['total_sources']}个RSS源 + DDG搜索, "
                f"共{results['total_items']}条, 新增{results['new_items']}条, 累计{stats['total']}条")
    return results