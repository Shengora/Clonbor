from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
import asyncio

from bot.database import db
from bot.core.userbot import userbot_manager

def get_main_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📱 Nomer olish"), KeyboardButton(text="💰 Balans")],
            [KeyboardButton(text="ℹ️ Ma'lumot")]
        ],
        resize_keyboard=True
    )
    return keyboard

async def start_command(message: types.Message):
    await db.add_user(message.from_user.id)
    await message.answer(
        "Assalomu alaykum! Xush kelibsiz.\n"
        "Quyidagi menyudan kerakli bo'limni tanlang:",
        reply_markup=get_main_keyboard()
    )

async def balance_handler(message: types.Message):
    user = await db.get_user(message.from_user.id)
    if user:
        await message.answer(
            f"💰 Sizning balansingiz: {user['balance']} so'm\n"
            f"🌟 Premium qilingan raqamlar: {user['premium_count']}"
        )
    else:
        await message.answer("Siz ro'yxatdan o'tmagansiz. Iltimos /start bosing.")

def create_inline_keyboard_from_source(source_markup) -> InlineKeyboardMarkup | None:
    if not source_markup or not source_markup.inline_keyboard:
        return None

    inline_keyboard = []
    for row in source_markup.inline_keyboard:
        new_row = []
        for button in row:
            # We map source button text to our callback data
            # Keep it simple: use text as callback data
            callback_data = f"source_btn:{button.text}"
            new_row.append(InlineKeyboardButton(text=button.text, callback_data=callback_data))
        inline_keyboard.append(new_row)

    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)

async def get_number_handler(message: types.Message):
    await message.answer("⏳ Raqam olinmoqda, kuting...")

    response = await userbot_manager.request_number(message.from_user.id)

    if response:
        keyboard = create_inline_keyboard_from_source(response.get("reply_markup"))
        await message.answer(response.get("text", "Raqam ma'lumotlari:"), reply_markup=keyboard)
    else:
        await message.answer("❌ Hozircha bo'sh raqamlar yo'q yoki manba bilan bog'lanishda xatolik yuz berdi.")

async def source_button_callback(callback_query: types.CallbackQuery):
    # Extract the button text that was pressed
    button_text = callback_query.data.split(":", 1)[1]

    await callback_query.message.edit_text("⏳ So'rov yuborilmoqda...")

    response = await userbot_manager.press_inline_button(callback_query.from_user.id, button_text)

    if response:
        text = response.get("text", "")
        keyboard = create_inline_keyboard_from_source(response.get("reply_markup"))

        await callback_query.message.edit_text(text, reply_markup=keyboard)

        # Check if premium was successfully activated
        if "premium activated and counted" in text.lower():
            user_price_str = await db.get_setting('user_price')
            user_price = int(user_price_str) if user_price_str else 5000

            await db.update_user_balance(callback_query.from_user.id, user_price)
            await db.increment_user_premium_count(callback_query.from_user.id)
            await db.update_statistics(user_price)

            await callback_query.message.answer(f"🎉 Tabriklaymiz! Premium muvaffaqiyatli faollashtirildi.\n💰 Balansingizga {user_price} so'm qo'shildi.")
    else:
        await callback_query.message.edit_text("❌ Amaliyotni bajarishda xatolik yuz berdi.")

def register_user_handlers(dp: Dispatcher):
    dp.message.register(start_command, Command("start"))
    dp.message.register(balance_handler, F.text == "💰 Balans")
    dp.message.register(get_number_handler, F.text == "📱 Nomer olish")
    dp.callback_query.register(source_button_callback, F.data.startswith("source_btn:"))
