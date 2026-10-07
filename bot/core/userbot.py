from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.handlers import MessageHandler
import asyncio
import logging
from collections import defaultdict

from bot.database import db
from bot.core.config import API_ID, API_HASH, SOURCE_BOT_USERNAME

logger = logging.getLogger(__name__)

class UserbotManager:
    def __init__(self):
        self.clients: dict[int, Client] = {}  # account_id -> Client
        self.active_requests: dict[int, dict] = {} # user_telegram_id -> {"client_id": int, "message_id": int}
        # Future queue mapping to handle concurrent requests to the source bot
        self.pending_requests = asyncio.Queue()
        self.response_events = defaultdict(asyncio.Event)
        self.response_data = {}
        self.client_locks = defaultdict(asyncio.Lock)

    async def start_all(self):
        accounts = await db.get_all_accounts()
        for account in accounts:
            if account['session_string']:
                client = Client(
                    name=f"session_{account['id']}",
                    session_string=account['session_string'],
                    api_id=API_ID,
                    api_hash=API_HASH,
                    in_memory=True
                )

                @client.on_message(filters.chat(SOURCE_BOT_USERNAME))
                @client.on_edited_message(filters.chat(SOURCE_BOT_USERNAME))
                async def handle_source_message(c: Client, m: Message):
                    # Basic mechanism: unlock the event when the bot replies.
                    # In a fully robust system, you'd match the response to the exact user request.
                    self.response_data[c.name] = m
                    self.response_events[c.name].set()

                try:
                    await client.start()
                    self.clients[account['id']] = client
                    logger.info(f"Started userbot for account ID {account['id']}")
                except Exception as e:
                    logger.error(f"Failed to start userbot {account['id']}: {e}")

    async def stop_all(self):
        for client in self.clients.values():
            await client.stop()

    async def request_number(self, user_telegram_id: int) -> dict | None:
        if not self.clients:
            logger.error("No active userbots available.")
            return None

        # Simplistic approach for now: grab the first available client.
        client_id, client = next(iter(self.clients.items()))

        async with self.client_locks[client.name]:
            self.response_events[client.name].clear()

            try:
                msg = await client.send_message(SOURCE_BOT_USERNAME, "/getNumber")

                # Wait for the event to be set by the message handler
                try:
                    await asyncio.wait_for(self.response_events[client.name].wait(), timeout=10.0)
                except asyncio.TimeoutError:
                    return None

                response = self.response_data.get(client.name)

                if response and response.id > msg.id:
                    self.active_requests[user_telegram_id] = {
                        "client_id": client_id,
                        "source_message_id": response.id
                    }
                    return {"text": response.text, "reply_markup": response.reply_markup}
                return None
            except Exception as e:
                logger.error(f"Error requesting number: {e}")
                return None

    async def press_inline_button(self, user_telegram_id: int, button_data: str) -> dict | None:
        request_info = self.active_requests.get(user_telegram_id)
        if not request_info:
            return None

        client_id = request_info["client_id"]
        source_message_id = request_info["source_message_id"]
        client = self.clients.get(client_id)

        if not client:
            return None

        async with self.client_locks[client.name]:
            self.response_events[client.name].clear()
            try:
                message = await client.get_messages(SOURCE_BOT_USERNAME, source_message_id)
                if message.reply_markup:
                    for row in message.reply_markup.inline_keyboard:
                        for button in row:
                            if button.text.lower() == button_data.lower() or button.callback_data == button_data:
                                await client.request_callback_answer(
                                    chat_id=SOURCE_BOT_USERNAME,
                                    message_id=source_message_id,
                                    callback_data=button.callback_data
                                )

                                try:
                                    await asyncio.wait_for(self.response_events[client.name].wait(), timeout=2.0)
                                except asyncio.TimeoutError:
                                    pass # Proceed to fetch anyway

                                edited_message = await client.get_messages(SOURCE_BOT_USERNAME, source_message_id)
                                return {"text": edited_message.text, "reply_markup": edited_message.reply_markup}
                return None
            except Exception as e:
                logger.error(f"Error pressing inline button: {e}")
                return None

userbot_manager = UserbotManager()
