"""News source parsers for Claude/Anthropic updates."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from xml.etree import ElementTree

import httpx
from bs4 import BeautifulSoup

from src.config import NEWS_SOURCES

logger = logging.getLogger(__name__)

CLAUDE_KEYWORDS = [
    "claude",
    "anthropic",
    "sonnet",
    "opus",
    "haiku",
    "claude code",
    "model card",
    "system prompt",
    "artifacts",
    "mcp",
    "model context protocol",
]


@dataclass
class Article:
    title: str
    url: str
    summary: str
    source: str

    @property
    def uid(self) -> str:
        return self.url


def _is_claude_related(text: str) -> bool:
    lower = text.lower()
    return any(kw in lower for kw in CLAUDE_KEYWORDS)


async def fetch_rss() -> list[Article]:
    """Parse the Anthropic RSS feed."""
    articles: list[Article] = []
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.get(NEWS_SOURCES["anthropic_rss"])
            resp.raise_for_status()
        root = ElementTree.fromstring(resp.text)
        # Handle both RSS and Atom namespaces
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        items = root.findall(".//item") or root.findall(".//atom:entry", ns)
        for item in items:
            title = (
                item.findtext("title")
                or item.findtext("atom:title", namespaces=ns)
                or ""
            )
            link = item.findtext("link") or ""
            if not link:
                link_el = item.find("atom:link", ns)
                link = link_el.get("href", "") if link_el is not None else ""
            desc = (
                item.findtext("description")
                or item.findtext("atom:summary", namespaces=ns)
                or ""
            )
            if _is_claude_related(f"{title} {desc}"):
                articles.append(
                    Article(
                        title=title,
                        url=link,
                        summary=BeautifulSoup(desc, "html.parser").get_text(
                            separator=" ", strip=True
                        ),
                        source="anthropic_rss",
                    )
                )
    except Exception:
        logger.exception("Failed to fetch RSS feed")
    return articles


async def fetch_anthropic_blog() -> list[Article]:
    """Scrape the Anthropic news/blog page for Claude-related posts."""
    articles: list[Article] = []
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.get(
                NEWS_SOURCES["anthropic_blog"],
                headers={"User-Agent": "ClaudeNewsBot/1.0"},
            )
            resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        for a_tag in soup.select("a[href*='/research/'], a[href*='/news/']"):
            href = a_tag.get("href", "")
            if not href:
                continue
            if href.startswith("/"):
                href = f"https://www.anthropic.com{href}"
            title = a_tag.get_text(strip=True)
            if not title or len(title) < 5:
                continue
            if _is_claude_related(title):
                articles.append(
                    Article(title=title, url=href, summary="", source="anthropic_blog")
                )
    except Exception:
        logger.exception("Failed to scrape Anthropic blog")
    return articles


async def fetch_all() -> list[Article]:
    """Fetch from all sources and deduplicate by URL."""
    rss_articles = await fetch_rss()
    blog_articles = await fetch_anthropic_blog()

    seen_urls: set[str] = set()
    unique: list[Article] = []
    for article in rss_articles + blog_articles:
        if article.url not in seen_urls:
            seen_urls.add(article.url)
            unique.append(article)
    return unique
