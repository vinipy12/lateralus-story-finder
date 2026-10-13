import logging

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, filters

from story_finder import messages
from story_finder.config import Settings

logger = logging.getLogger(__name__)


class Handlers:
    """Telegram command handlers.

    Every path replies to the Owner; none is silent. Silence toward the Owner is
    indistinguishable from a dead bot, which is this design's main failure mode.
    """

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await update.message.reply_text(messages.START)


async def on_error(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log in English, reply in pt-BR. A stack trace never reaches the Owner."""
    logger.exception("unhandled error while processing update", exc_info=context.error)
    if isinstance(update, Update) and update.message is not None:
        await update.message.reply_text(messages.UNEXPECTED_ERROR)


def build_application(settings: Settings) -> Application:
    """Wire handlers behind an Owner-only filter.

    Updates from anyone else match no handler and so receive no response at all —
    not a refusal, silence. The bot does not advertise itself to strangers.
    """
    application = Application.builder().token(settings.telegram_bot_token).build()
    handlers = Handlers()
    owner_only = filters.User(user_id=settings.telegram_owner_id)

    application.add_handler(CommandHandler("start", handlers.start, filters=owner_only))
    application.add_error_handler(on_error)
    return application
