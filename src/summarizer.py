"""Summarize articles by fetching their full content and condensing it."""

from __future__ import annotations

import logging

import httpx
from bs4 import BeautifulSoup

from src.sources import Article

logger = logging.getLogger(__name__)

MAX_CONTENT_LENGTH = 4000


async def _fetch_article_body(url: str) -> str:
    """Fetch and extract readable text from an article URL."""
    try:
        async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
            resp = await client.get(
                url, headers={"User-Agent": "ClaudeNewsBot/1.0"}
            )
            resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        # Remove nav, footer, script, style
        for tag in soup(["nav", "footer", "script", "style", "header"]):
            tag.decompose()
        text = soup.get_text(separator=" ", strip=True)
        return text[:MAX_CONTENT_LENGTH]
    except Exception:
        logger.exception("Failed to fetch article body: %s", url)
        return ""


def _extractive_summary(text: str, max_sentences: int = 5) -> str:
    """Simple extractive summary: take the first N sentences."""
    if not text:
        return "No content available."
    sentences = []
    for part in text.replace("\n", " ").split("."):
        part = part.strip()
        if len(part) > 20:
            sentences.append(part + ".")
        if len(sentences) >= max_sentences:
            break
    return " ".join(sentences) if sentences else text[:500]


async def summarize(article: Article) -> str:
    """Return a summary for the given article."""
    body = await _fetch_article_body(article.url)
    # Use the RSS summary if available, otherwise extract from body
    text = article.summary if article.summary else body
    return _extractive_summary(text)


def format_update(article: Article, summary: str) -> str:
    """Format an article + summary as a Telegram message (HTML)."""
    return (
        f"<b>📰 {_escape_html(article.title)}</b>\n\n"
        f"{_escape_html(summary)}\n\n"
        f'<a href="{article.url}">Read more →</a>\n'
        f"<i>Source: {article.source}</i>"
    )


def _escape_html(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
