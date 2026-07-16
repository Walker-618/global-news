"""Test RSS feeds"""
import feedparser, httpx, sys, json

feeds = [
    ("Ars Technica","https://feeds.arstechnica.com/arstechnica/index","TECH"),
    ("MIT Tech Review","https://www.technologyreview.com/feed/","AI"),
    ("Wired","https://www.wired.com/feed/rss","TECH"),
    ("CNET","https://www.cnet.com/rss/news/","TECH"),
    ("Engadget","https://www.engadget.com/rss.xml","TECH"),
    ("OpenAI Blog","https://openai.com/blog/rss.xml","AI"),
    ("MarketWatch","https://feeds.marketwatch.com/marketwatch/topstories","FINANCE"),
    ("BBC News","https://feeds.bbci.co.uk/news/rss.xml","TECH"),
    ("NPR","https://feeds.npr.org/1001/rss.xml","TECH"),
    ("VentureBeat","https://venturebeat.com/feed/","AI"),
    ("New Scientist","https://www.newscientist.com/feed/home","TECH"),
    ("Google AI","https://blog.research.google/feed/","AI"),
    ("Yahoo Finance","https://finance.yahoo.com/news/rssindex","FINANCE"),
    ("CNBC Finance","https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=100003114","FINANCE"),
    ("The Register","https://www.theregister.com/headlines.rss","TECH"),
    ("ZDNet","https://www.zdnet.com/news/rss.xml","TECH"),
]

headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
ok_count = 0
for name, url, cat in feeds:
    try:
        r = httpx.get(url, timeout=15, headers=headers, follow_redirects=True)
        f = feedparser.parse(r.text)
        count = len(f.entries)
        has_img = any("media_thumbnail" in e or "media_content" in e or "summary" in e for e in f.entries[:3])
        print(f"{'✅' if count>0 else '❌'} [{cat}] {name}: {count}条 {'📷' if has_img else '  '}")
        ok_count += 1 if count > 0 else 0
    except Exception as e:
        print(f"❌ [{cat}] {name}: {str(e)[:50]}")

print(f"\n{ok_count}/{len(feeds)} ok")