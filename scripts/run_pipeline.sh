#!/usr/bin/env bash
# 完整流水线（全量采集+构建）
cd /c/Users/cole/hermes/01-全球AI科技财经资讯聚合 && .venv/Scripts/python.exe scripts/fetch_once.py 2>&1 && .venv/Scripts/python.exe scripts/build.py 2>&1