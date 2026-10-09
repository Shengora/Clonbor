import asyncio
import logging
from aiogram import Bot

logger = logging.getLogger(__name__)

class Forwarder:
    def __init__(self):
        self.bot: Bot = None

    def set_bot(self, bot: Bot):
        self.bot = bot

    async def forward_edit(self, user_telegram_id: int, user_message_id: int, source_message_id: int, new_text: str, reply_markup):
        if not self.bot:
            return

        try:
            # Import dynamically to avoid circular dependencies
            from bot.handlers.user import create_inline_keyboard_from_source, handle_premium_stats

            keyboard = create_inline_keyboard_from_source(reply_markup)

            await self.bot.edit_message_text(
                chat_id=user_telegram_id,
                message_id=user_message_id,
                text=new_text,
                reply_markup=keyboard
            )

            # Process stats (e.g. premium activated, canceled)
            await handle_premium_stats(user_telegram_id, source_message_id, new_text)

        except Exception as e:
            # We might hit Message is not modified, which is fine
            if "message is not modified" not in str(e).lower():
                logger.error(f"Error forwarding edit to user {user_telegram_id}: {e}")

forwarder = Forwarder()
