import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_IDS = [
    int(cid.strip())
    for cid in os.environ.get("TELEGRAM_CHAT_IDS", "").split(",")
    if cid.strip()
]
POLL_INTERVAL_MINUTES = int(os.environ.get("POLL_INTERVAL_MINUTES", "30"))

SEEN_ARTICLES_FILE = "data/seen_articles.json"

NEWS_SOURCES = {
    "anthropic_blog": "https://www.anthropic.com/news",
    "anthropic_rss": "https://www.anthropic.com/rss.xml",
}
