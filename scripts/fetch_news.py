import os
import re
import time
from datetime import datetime, timezone

import requests

from dotenv import load_dotenv

load_dotenv()  
API_BASE_URL = "http://localhost:8000"
NEWSAPI_URL = "https://newsapi.org/v2/top-headlines"


def fetch_news(api_key: str, page_size: int = 20):
    try:
        response = requests.get(
            NEWSAPI_URL,
            params={"language": "en", "pageSize": page_size, "apiKey": api_key},
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
        return data.get("articles", [])
    except requests.RequestException as exc:
        print(f"Error fetching news: {exc}")
        return []


def publish_article(article: dict):
    title = article.get("title")
    if title is None or title == "[Removed]":
        print(f"Skipping article with removed title: {article.get('url', 'unknown')}")
        return

    content = article.get("content")
    if content is None:
        print(f"Skipping article with no content: {title}")
        return

    content = re.sub(r"\s*\[\+\d+\s+chars\]\s*$", "", content).strip()

    url = article.get("url", "")
    payload = {
        "id": str(abs(hash(url))),
        "title": title,
        "content": content,
        "source": article.get("source", {}).get("name") or "Unknown",
        "timestamp": article.get("publishedAt") or datetime.now(timezone.utc).isoformat(),
    }

    try:
        response = requests.post(
            f"{API_BASE_URL}/news",
            json=payload,
            timeout=10,
        )
        response.raise_for_status()
        print(f"Published article: {title}")
    except requests.RequestException as exc:
        print(f"Error publishing article '{title}': {exc}")

    time.sleep(0.2)


def main():
    api_key = os.environ.get("NEWS_API_KEY")
    if not api_key:
        raise SystemExit("NEWS_API_KEY not found. Please set it in your environment.")

    articles = fetch_news(api_key)
    print(f"Found {len(articles)} articles")

    for article in articles:
        publish_article(article)

    print("Done!")


if __name__ == "__main__":
    main()