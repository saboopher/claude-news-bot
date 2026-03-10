"""Telegram bot commands and scheduled job."""

from __future__ import annotations

import logging

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)

from src import sources, store
from src.config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_IDS
from src.summarizer import format_update, summarize

logger = logging.getLogger(__name__)


async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "👋 Hi! I track Claude / Anthropic news.\n\n"
        "Commands:\n"
        "/latest – fetch latest Claude news now\n"
        "/status – show bot status"
    )


async def cmd_status(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    seen = store.load_seen()
    await update.message.reply_text(
        f"Tracking {len(seen)} articles so far.\n"
        f"Subscribed chats: {len(TELEGRAM_CHAT_IDS)}"
    )


async def cmd_latest(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """Manually trigger a news check and reply in the same chat."""
    await update.message.reply_text("🔍 Checking for Claude news…")
    articles = await sources.fetch_all()
    if not articles:
        await update.message.reply_text("No Claude-related news found right now.")
        return

    seen = store.load_seen()
    new_articles = [a for a in articles if a.uid not in seen]

    if not new_articles:
        await update.message.reply_text("No new articles since last check.")
        return

    for article in new_articles[:5]:
        summary = await summarize(article)
        msg = format_update(article, summary)
        await update.message.reply_text(msg, parse_mode="HTML", disable_web_page_preview=True)
        seen.add(article.uid)

    store.save_seen(seen)
    await update.message.reply_text(f"✅ Sent {len(new_articles[:5])} update(s).")


async def scheduled_check(ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """Run by the scheduler to push new articles to subscribed chats."""
    articles = await sources.fetch_all()
    seen = store.load_seen()
    new_articles = [a for a in articles if a.uid not in seen]

    if not new_articles:
        return

    for article in new_articles:
        summary = await summarize(article)
        msg = format_update(article, summary)
        for chat_id in TELEGRAM_CHAT_IDS:
            try:
                await ctx.bot.send_message(
                    chat_id, msg, parse_mode="HTML", disable_web_page_preview=True
                )
            except Exception:
                logger.exception("Failed to send to chat %s", chat_id)
        seen.add(article.uid)

    store.save_seen(seen)
    logger.info("Sent %d new article(s)", len(new_articles))


def build_app() -> Application:
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("latest", cmd_latest))
    return app
