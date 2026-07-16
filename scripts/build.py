#!/usr/bin/env python
"""
构建脚本 — 从 data/ 生成静态页面到 dist/
用法: python scripts/build.py
"""

import logging
import os
import shutil
import sys
import time

sys.path.insert(0, ".")

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")
logger = logging.getLogger("build")

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST_DIR = os.path.join(PROJECT_DIR, "dist")


def clean_dist():
    """清空 dist 目录"""
    if os.path.exists(DIST_DIR):
        shutil.rmtree(DIST_DIR)
    os.makedirs(DIST_DIR, exist_ok=True)
    logger.info("已清空 dist/")


def copy_static():
    """复制静态资源"""
    # 复制 tag-page.html (作为备用JS版本，实际使用服务器生成的页面)
    src_tag = os.path.join(PROJECT_DIR, "tag-page.html")
    if os.path.exists(src_tag):
        shutil.copy2(src_tag, os.path.join(DIST_DIR, "tag-page-js.html"))
    logger.info("已复制静态资源")


def main():
    logger.info("=" * 50)
    logger.info("开始构建")
    logger.info("=" * 50)

    start = time.time()

    clean_dist()
    copy_static()

    from src.generators.index_generator import generate_index
    from src.generators.tag_generator import generate_tag_pages

    index_path = generate_index()
    tag_dir = generate_tag_pages()

    elapsed = time.time() - start
    logger.info("=" * 50)
    logger.info(f"构建完成! 耗时 {elapsed:.1f}秒")
    logger.info(f"  index.html: {index_path}")
    logger.info(f"  tag-pages: {tag_dir}")
    logger.info("=" * 50)

    return 0


if __name__ == "__main__":
    sys.exit(main())