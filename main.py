"""Entry point for the Claude News Bot."""

import logging

from src.bot import build_app, scheduled_check
from src.config import POLL_INTERVAL_MINUTES

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def main() -> None:
    app = build_app()

    # Schedule periodic news checks
    app.job_queue.run_repeating(
        scheduled_check,
        interval=POLL_INTERVAL_MINUTES * 60,
        first=10,  # first run 10s after startup
    )
    logger.info(
        "Bot starting – polling every %d minutes", POLL_INTERVAL_MINUTES
    )
    app.run_polling()


if __name__ == "__main__":
    main()
