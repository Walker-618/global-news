"""
存储引擎 — JSON 文件读写 + 去重
"""

import json
import os
import re
from datetime import datetime, timezone
from typing import List, Optional, Set

from src.models import NewsItem, ALL_CATEGORIES


DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
MAX_ITEMS_PER_CATEGORY = 50


def _category_dir(category: str) -> str:
    d = os.path.join(DATA_DIR, "news", category)
    os.makedirs(d, exist_ok=True)
    return d


def _today_file(category: str) -> str:
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return os.path.join(_category_dir(category), f"{date_str}.json")


def _index_file() -> str:
    return os.path.join(DATA_DIR, "index.json")


def load_items(category: str, limit: int = MAX_ITEMS_PER_CATEGORY) -> List[NewsItem]:
    """加载指定分类的最新 N 条新闻"""
    cat_dir = _category_dir(category)
    if not os.path.isdir(cat_dir):
        return []

    # 读取所有日期的文件，取最新 limit 条
    files = sorted(
        [f for f in os.listdir(cat_dir) if f.endswith(".json")],
        reverse=True,
    )
    items: List[NewsItem] = []
    for fname in files:
        if len(items) >= limit:
            break
        fpath = os.path.join(cat_dir, fname)
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                data = json.load(f)
            for d in data:
                if len(items) >= limit:
                    break
                items.append(NewsItem.from_dict(d))
        except (json.JSONDecodeError, IOError):
            continue
    return items


def _normalize_title(title: str) -> str:
    """归一化标题用于去重比较"""
    t = title.lower()
    t = re.sub(r"[^a-z0-9\u4e00-\u9fff]", "", t)  # 只保留字母数字汉字
    t = re.sub(r"(breaking|exclusive|update|live|justin)", "", t)
    return t[:60]


def save_items(category: str, items: List[NewsItem]) -> int:
    """保存新条目到当日文件，返回新增数量"""
    fpath = _today_file(category)
    existing_ids = set()
    existing_titles = set()
    existing_items: List[dict] = []

    # 读取已有
    if os.path.exists(fpath):
        with open(fpath, "r", encoding="utf-8") as f:
            try:
                existing_items = json.load(f)
                existing_ids = {e["id"] for e in existing_items}
                existing_titles = {_normalize_title(e.get("title", "")) for e in existing_items}
            except json.JSONDecodeError:
                existing_items = []

    # 去重追加（URL hash + 标题相似）
    new_count = 0
    for item in items:
        norm_title = _normalize_title(item.title)
        if item.id not in existing_ids and norm_title not in existing_titles:
            existing_items.append(item.to_dict())
            existing_ids.add(item.id)
            existing_titles.add(norm_title)
            new_count += 1

    # 限制文件大小（最多保留200条/天/分类）
    if len(existing_items) > 200:
        existing_items = existing_items[-200:]

    with open(fpath, "w", encoding="utf-8") as f:
        json.dump(existing_items, f, ensure_ascii=False, indent=2)

    # 更新索引
    _rebuild_index()

    return new_count


def _rebuild_index():
    """重建汇总索引：各分类最新50条"""
    index = {}
    for cat in ALL_CATEGORIES:
        items = load_items(cat, MAX_ITEMS_PER_CATEGORY)
        index[cat] = [item.to_dict() for item in items]

    index["_meta"] = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "total": sum(len(v) for k, v in index.items() if not k.startswith("_")),
        "counts": {cat: len(index[cat]) for cat in ALL_CATEGORIES},
    }

    with open(_index_file(), "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)


def get_index() -> dict:
    """读取索引"""
    if os.path.exists(_index_file()):
        with open(_index_file(), "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def get_stats() -> dict:
    """获取统计信息"""
    idx = get_index()
    meta = idx.get("_meta", {})
    return {
        "updated_at": meta.get("updated_at", "从未更新"),
        "total": meta.get("total", 0),
        "counts": meta.get("counts", {}),
    }