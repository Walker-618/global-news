"""存储引擎 — JSON 文件读写 + 去重"""

import json, os, re
from datetime import datetime, timezone
from typing import List, Set

from src.models import NewsItem, ALL_CATEGORIES

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
MAX_PER_CAT = 50

def _cat_dir(cat: str) -> str:
    d = os.path.join(DATA_DIR, "news", cat)
    os.makedirs(d, exist_ok=True); return d

def _today(cat: str) -> str:
    return os.path.join(_cat_dir(cat), f"{datetime.now(timezone.utc).strftime('%Y-%m-%d')}.json")

def _idx() -> str:
    return os.path.join(DATA_DIR, "index.json")

def load_items(cat: str, limit: int = MAX_PER_CAT) -> List[NewsItem]:
    """加载指定分类的最新 N 条 (按入库逆序 = 最新在前)"""
    cd = _cat_dir(cat)
    if not os.path.isdir(cd): return []
    items = []
    for fname in sorted([f for f in os.listdir(cd) if f.endswith(".json")], reverse=True):
        if len(items) >= limit: break
        try:
            with open(os.path.join(cd, fname), encoding="utf-8") as f:
                data = json.load(f)
            for d in reversed(data):  # 文件末尾 = 最新入库
                if len(items) >= limit: break
                items.append(NewsItem.from_dict(d))
        except: continue
    items.sort(key=lambda x: x.published_at or "1900", reverse=True)
    return items

def _norm_title(t: str) -> str:
    t = t.lower()
    t = re.sub(r"[^a-z0-9\u4e00-\u9fff]", "", t)
    return t[:60]

def save_items(cat: str, items: List[NewsItem]) -> int:
    fp = _today(cat)
    exist, eids, etitles = [], set(), set()
    if os.path.exists(fp):
        with open(fp, encoding="utf-8") as f:
            try:
                exist = json.load(f)
                eids = {e["id"] for e in exist}
                etitles = {_norm_title(e.get("title","")) for e in exist}
            except: exist = []
    new = 0
    for it in items:
        nt = _norm_title(it.title)
        if it.id not in eids and nt not in etitles:
            exist.append(it.to_dict())
            eids.add(it.id); etitles.add(nt); new += 1
    if len(exist) > 200: exist = exist[-200:]
    with open(fp, "w", encoding="utf-8") as f:
        json.dump(exist, f, ensure_ascii=False, indent=2)
    _rebuild(); return new

def _rebuild():
    idx = {}
    for cat in ALL_CATEGORIES:
        items = load_items(cat, MAX_PER_CAT)
        idx[cat] = [i.to_dict() for i in items]
    idx["_meta"] = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "total": sum(len(v) for k,v in idx.items() if not k.startswith("_")),
        "counts": {c: len(idx[c]) for c in ALL_CATEGORIES},
    }
    with open(_idx(), "w", encoding="utf-8") as f:
        json.dump(idx, f, ensure_ascii=False, indent=2)

def get_index() -> dict:
    if os.path.exists(_idx()):
        with open(_idx(), encoding="utf-8") as f: return json.load(f)
    return {}

def get_stats() -> dict:
    m = get_index().get("_meta", {})
    return {"updated_at": m.get("updated_at","从未更新"), "total": m.get("total",0), "counts": m.get("counts",{})}