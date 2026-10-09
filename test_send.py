import asyncio
from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import os

from dotenv import load_dotenv
load_dotenv()
token = os.getenv("BOT_TOKEN")
admin_ids = os.getenv("ADMIN_IDS").split(",")

async def main():
    bot = Bot(token=token)
    try:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Test", callback_data="test", style="danger")]
        ])
        await bot.send_message(chat_id=admin_ids[0], text="Test style", reply_markup=kb)
        print("Successfully sent with style!")
    except Exception as e:
        print("Failed to send:", type(e), e)
    finally:
        await bot.session.close()

asyncio.run(main())
