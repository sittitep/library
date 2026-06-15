#!/usr/bin/env python3
import json
import os
import shutil
from pathlib import Path

ARTICLES_DIR = Path("data/articles")
SITE_DIR = Path("_site")

def load_articles():
    articles = []
    for article_dir in sorted(ARTICLES_DIR.iterdir()):
        if not article_dir.is_dir():
            continue
        meta_path = article_dir / "meta.json"
        content_path = article_dir / "content.html"
        if not meta_path.exists() or not content_path.exists():
            continue
        with open(meta_path) as f:
            meta = json.load(f)
        articles.append({"meta": meta, "content_path": content_path})
    return articles

def build_article_page(article, site_dir):
    meta = article["meta"]
    slug = meta["seo"]["slug"]
    out_dir = site_dir / "blog" / slug
    out_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy(article["content_path"], out_dir / "index.html")

def build_index(articles, site_dir):
    cards_html = ""
    for article in articles:
        meta = article["meta"]
        seo = meta["seo"]
        wiki = meta.get("wiki", {})
        slug = seo["slug"]
        title = seo["title"]
        description = seo["description"]
        reading_time = wiki.get("estimated_reading_time_minutes", "")
        tags = wiki.get("tags", [])[:5]
        categories = wiki.get("categories", [])

        tags_html = "".join(f'<span class="tag">{t}</span>' for t in tags)
        category = categories[0] if categories else ""
        reading_str = f"{reading_time} min read" if reading_time else ""

        cards_html += f"""
    <article class="card">
      <div class="card-meta">
        {"<span class='category'>" + category + "</span>" if category else ""}
        {"<span class='reading-time'>" + reading_str + "</span>" if reading_str else ""}
      </div>
      <h2><a href="/blog/{slug}/">{title}</a></h2>
      <p class="description">{description}</p>
      <div class="tags">{tags_html}</div>
    </article>"""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Library</title>
  <meta name="description" content="A personal library of technical articles and tutorials." />
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    :root {{
      --bg: #fafaf8;
      --surface: #ffffff;
      --border: #e8e6e1;
      --text: #1a1a1a;
      --text-muted: #6b6860;
      --accent: #2563eb;
      --tag-bg: #f1f0ed;
      --tag-text: #4a4742;
    }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif;
      background: var(--bg);
      color: var(--text);
      line-height: 1.6;
      min-height: 100vh;
    }}
    header {{
      border-bottom: 1px solid var(--border);
      padding: 1.5rem 0;
    }}
    .container {{
      max-width: 720px;
      margin: 0 auto;
      padding: 0 1.5rem;
    }}
    .site-name {{
      font-size: 1.1rem;
      font-weight: 600;
      letter-spacing: -0.01em;
      color: var(--text);
      text-decoration: none;
    }}
    .site-name:hover {{ color: var(--accent); }}
    main {{ padding: 3rem 0; }}
    .page-heading {{
      font-size: 0.8rem;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: var(--text-muted);
      margin-bottom: 2rem;
    }}
    .card {{
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 1.75rem;
      margin-bottom: 1.25rem;
      transition: border-color 0.15s, box-shadow 0.15s;
    }}
    .card:hover {{
      border-color: #c8c6c1;
      box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    }}
    .card-meta {{
      display: flex;
      align-items: center;
      gap: 1rem;
      margin-bottom: 0.6rem;
    }}
    .category {{
      font-size: 0.72rem;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.07em;
      color: var(--accent);
    }}
    .reading-time {{
      font-size: 0.8rem;
      color: var(--text-muted);
    }}
    .card h2 {{
      font-size: 1.15rem;
      font-weight: 600;
      letter-spacing: -0.02em;
      line-height: 1.35;
      margin-bottom: 0.6rem;
    }}
    .card h2 a {{
      color: var(--text);
      text-decoration: none;
    }}
    .card h2 a:hover {{ color: var(--accent); }}
    .description {{
      font-size: 0.9rem;
      color: var(--text-muted);
      line-height: 1.55;
      margin-bottom: 1rem;
    }}
    .tags {{ display: flex; flex-wrap: wrap; gap: 0.4rem; }}
    .tag {{
      font-size: 0.72rem;
      background: var(--tag-bg);
      color: var(--tag-text);
      padding: 0.2rem 0.55rem;
      border-radius: 4px;
      font-weight: 500;
    }}
    footer {{
      border-top: 1px solid var(--border);
      padding: 1.5rem 0;
      text-align: center;
      font-size: 0.8rem;
      color: var(--text-muted);
    }}
    @media (max-width: 600px) {{
      .card {{ padding: 1.25rem; }}
      .card h2 {{ font-size: 1.05rem; }}
    }}
  </style>
</head>
<body>
  <header>
    <div class="container">
      <a class="site-name" href="/">Library</a>
    </div>
  </header>
  <main>
    <div class="container">
      <p class="page-heading">All articles</p>
      {cards_html}
    </div>
  </main>
  <footer>
    <div class="container">Built from <code>data/articles/</code></div>
  </footer>
</body>
</html>"""

    (site_dir / "index.html").write_text(html)

def main():
    if SITE_DIR.exists():
        shutil.rmtree(SITE_DIR)
    SITE_DIR.mkdir()
    (SITE_DIR / ".nojekyll").touch()

    articles = load_articles()
    for article in articles:
        build_article_page(article, SITE_DIR)
    build_index(articles, SITE_DIR)
    print(f"Built {len(articles)} article(s) to {SITE_DIR}/")

if __name__ == "__main__":
    main()
