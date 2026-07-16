#!/usr/bin/env python
"""
手动触发一次采集 — 测试用
用法: python scripts/fetch_once.py [--domestic]
"""

import logging
import sys
import time

# 确保项目根目录在路径中
sys.path.insert(0, ".")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)

from src.pipeline import run_pipeline


def main():
    only_domestic = "--domestic" in sys.argv

    logger = logging.getLogger("fetch_once")
    logger.info("=" * 50)
    logger.info("开始采集" + ("(仅国内源)" if only_domestic else "(全部源)"))
    logger.info("=" * 50)

    start = time.time()
    results = run_pipeline(only_domestic=only_domestic)
    elapsed = time.time() - start
    results["duration_seconds"] = round(elapsed, 1)

    logger.info("=" * 50)
    logger.info(f"采集完成! 耗时 {elapsed:.1f}秒")
    logger.info(f"  数据源: {results['succeeded']}/{results['total_sources']} 成功")
    logger.info(f"  获取: {results['total_items']} 条")
    logger.info(f"  新增: {results['new_items']} 条")
    logger.info(f"  累计: {results['storage']['total']} 条")
    logger.info(f"  各分类: {results['storage']['counts']}")
    logger.info("=" * 50)

    return 0 if results["succeeded"] > 0 else 1


if __name__ == "__main__":
    sys.exit(main())