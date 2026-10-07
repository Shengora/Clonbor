from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.handlers import MessageHandler
import asyncio
import logging
from collections import defaultdict

from bot.database import db
from bot.core.config import API_ID, API_HASH, SOURCE_BOT_USERNAME

async def dynamic_source_filter(_, __, message: Message):
    active_source = await db.get_setting("source_bot")
    if not active_source:
        from bot.core.config import SOURCE_BOT_USERNAME
        active_source = SOURCE_BOT_USERNAME

    if message.chat and message.chat.username:
        return message.chat.username.lower() == active_source.replace("@", "").lower()
    return False

source_filter = filters.create(dynamic_source_filter)


logger = logging.getLogger(__name__)

class UserbotManager:
    def __init__(self):
        self.clients: dict[int, Client] = {}  # account_id -> Client

        # New asynchronous routing table:
        # Maps source_bot message.id -> {"user_telegram_id": int, "user_message_id": int}
        self.routing_table: dict[int, dict] = {}

        # active_requests now used just for the initial wait loop.
        self.active_requests: dict[int, dict] = {}

        self.response_events = defaultdict(asyncio.Event)
        self.response_data = {}


    async def _get_active_source(self):
        active_source = await db.get_setting("source_bot")
        if not active_source:
            active_source = SOURCE_BOT_USERNAME
        return active_source

    async def start_account(self, account_id: int, session_string: str):
        if not session_string:
            return

        client = Client(
            name=f"session_{account_id}",
            session_string=session_string,
            api_id=API_ID,
            api_hash=API_HASH,
            in_memory=True
        )

        @client.on_message(source_filter)
        async def handle_source_message(c: Client, m: Message):
            self.response_data[c.name] = m
            self.response_events[c.name].set()

        @client.on_edited_message(source_filter)
        async def handle_edited_source_message(c: Client, m: Message):
            # This is where SMS codes or status changes arrive. We forward them.
            if m.id in self.routing_table:
                route = self.routing_table[m.id]
                from bot.core.forwarder import forwarder
                await forwarder.forward_edit(
                    user_telegram_id=route["user_telegram_id"],
                    user_message_id=route["user_message_id"],
                    new_text=m.text,
                    reply_markup=m.reply_markup
                )

        try:
            await client.start()
            # Resolve peer to cache it in memory and avoid Peer id invalid exceptions
            active_source = await self._get_active_source()
            try:
                await client.get_users(active_source)
            except Exception as peer_e:
                logger.warning(f"Could not preemptively resolve peer {active_source}: {peer_e}")

            self.clients[account_id] = client
            logger.info(f"Started userbot for account ID {account_id}")
        except Exception as e:
            logger.error(f"Failed to start userbot {account_id}: {e}")

    async def start_all(self):
        accounts = await db.get_all_accounts()
        for account in accounts:
            await self.start_account(account['id'], account['session_string'])

    async def stop_all(self):
        for client in self.clients.values():
            await client.stop()

    async def request_number(self, user_telegram_id: int, user_message_id: int) -> dict | None:
        if not self.clients:
            logger.error("No active userbots available.")
            return None

        # Simplistic approach for now: grab the first available client.
        client_id, client = next(iter(self.clients.items()))

        self.response_events[client.name].clear()

        try:
            msg = await client.send_message(await self._get_active_source(), "/getNumber")

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
                # Register route so background edits flow back to the user
                self.routing_table[response.id] = {
                    "user_telegram_id": user_telegram_id,
                    "user_message_id": user_message_id
                }
                return {"text": response.text, "reply_markup": response.reply_markup}
            return None
        except Exception as e:
            logger.error(f"Error requesting number: {e}")
            return None

    async def press_inline_button(self, user_telegram_id: int, button_data: str) -> bool:
        request_info = self.active_requests.get(user_telegram_id)
        if not request_info:
            return False

        client_id = request_info["client_id"]
        source_message_id = request_info["source_message_id"]
        client = self.clients.get(client_id)

        if not client:
            return False

        try:
            message = await client.get_messages(await self._get_active_source(), source_message_id)
            if message.reply_markup:
                for row in message.reply_markup.inline_keyboard:
                    for button in row:
                        if button.text.lower() == button_data.lower() or button.callback_data == button_data:
                            # Send callback asynchronously. We don't wait for a reply here!
                            # Pyrogram's handle_edited_source_message will catch the edit.
                            asyncio.create_task(
                                client.request_callback_answer(
                                    chat_id=await self._get_active_source(),
                                    message_id=source_message_id,
                                    callback_data=button.callback_data
                                )
                            )
                            return True
            return False
        except Exception as e:
            logger.error(f"Error pressing inline button: {e}")
            return False

userbot_manager = UserbotManager()
