from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import asyncio

from bot.database import db
from bot.core.userbot import userbot_manager

def get_main_keyboard():
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="My Stats", callback_data="user:stats")],
            [InlineKeyboardButton(text="Yordamchi", callback_data="user:help")],
            [InlineKeyboardButton(text="Pul yechish", callback_data="user:withdraw")],
            [InlineKeyboardButton(text="Mening kartalarim", callback_data="user:cards")]
        ]
    )
    return keyboard

def get_reply_keyboard():
    return types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="Yordamchi")]
        ],
        resize_keyboard=True
    )

async def start_command(message: types.Message):
    await db.add_user(message.from_user.id)

    await message.answer("🛠 Menyu:", reply_markup=get_reply_keyboard())

    await message.answer(
        "👋 Xush kelibsiz!\n\n"
        "Raqam olish uchun /getNumber yozing.",
        reply_markup=get_main_keyboard()
    )

async def stats_handler(callback_query: types.CallbackQuery):
    user = await db.get_user(callback_query.from_user.id)
    if user:
        # Calculate total numbers
        total_numbers = user['premium_count'] + user['canceled_numbers'] + user['frozen_numbers']

        await callback_query.message.answer(
            f"📊 Your Personal Stats:\n\n"
            f"📞 My Numbers (Total): {total_numbers}\n"
            f"❌ Canceled Numbers: {user['canceled_numbers']}\n"
            f"🧊 Frozen Numbers: {user['frozen_numbers']}\n"
            f"📨 Codes received: {user['codes_received']}\n"
            f"⭐ Premium numbers: {user['premium_count']}\n\n"
            f"💰 Balans: {user['balance']} so'm"
        )
    else:
        await callback_query.message.answer("Siz ro'yxatdan o'tmagansiz. Iltimos /start bosing.")
    await callback_query.answer()

async def help_handler(callback_query: types.CallbackQuery):
    await callback_query.message.answer("📞 Yordamchi bo'limiga xush kelibsiz.\n\nSavollaringiz bo'lsa yoki yordam kerak bo'lsa adminga murojaat qiling.")
    await callback_query.answer()

async def withdraw_handler(callback_query: types.CallbackQuery):
    await callback_query.message.answer("💸 Pul yechish bo'limi tez kunda ishga tushadi.")
    await callback_query.answer()

async def cards_handler(callback_query: types.CallbackQuery):
    await callback_query.message.answer("💳 Mening kartalarim bo'limi tez kunda ishga tushadi.")
    await callback_query.answer()

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

async def get_number_command(message: types.Message):
    msg = await message.answer("⏳ Raqam olinmoqda, kuting...")

    response = await userbot_manager.request_number(message.from_user.id, msg.message_id)

    if response:
        keyboard = create_inline_keyboard_from_source(response.get("reply_markup"))
        await msg.edit_text(response.get("text", "Raqam ma'lumotlari:"), reply_markup=keyboard)
    else:
        await msg.edit_text("❌ Hozircha bo'sh raqamlar yo'q yoki manba bilan bog'lanishda xatolik yuz berdi.")

async def get_number_handler(callback_query: types.CallbackQuery):
    msg = await callback_query.message.answer("⏳ Raqam olinmoqda, kuting...")
    await callback_query.answer()

    response = await userbot_manager.request_number(callback_query.from_user.id, msg.message_id)

    if response:
        keyboard = create_inline_keyboard_from_source(response.get("reply_markup"))
        await msg.edit_text(response.get("text", "Raqam ma'lumotlari:"), reply_markup=keyboard)
    else:
        await msg.edit_text("❌ Hozircha bo'sh raqamlar yo'q yoki manba bilan bog'lanishda xatolik yuz berdi.")

async def handle_premium_stats(user_telegram_id: int, text: str):
    lower_text = text.lower()

    if "premium activated and counted" in lower_text:
        user_price_str = await db.get_setting('user_price')
        user_price = int(user_price_str) if user_price_str else 5000

        # Prevent double-spending: check if this specific text was already processed (a more robust DB state could be used here)
        # For simplicity, we just increment. (In a real app, track source_message_id)
        await db.update_user_balance(user_telegram_id, user_price)
        await db.increment_user_premium_count(user_telegram_id)
        await db.update_statistics(user_price)

        from bot.core.forwarder import forwarder
        if forwarder.bot:
            await forwarder.bot.send_message(user_telegram_id, f"🎉 Tabriklaymiz! Premium muvaffaqiyatli faollashtirildi.\n💰 Balansingizga {user_price} so'm qo'shildi.")

    elif "cancel" in lower_text or "bekor qilindi" in lower_text:
        await db.increment_user_canceled_numbers(user_telegram_id)

    elif "frozen" in lower_text or "muzlatildi" in lower_text:
        await db.increment_user_frozen_numbers(user_telegram_id)

    elif "code" in lower_text or "kod:" in lower_text:
        await db.increment_user_codes_received(user_telegram_id)

async def source_button_callback(callback_query: types.CallbackQuery):
    button_text = callback_query.data.split(":", 1)[1]

    # We don't block and wait. We just send the press action to Pyrogram.
    success = await userbot_manager.press_inline_button(callback_query.from_user.id, button_text)

    if success:
        # Just answer the query. The background task will edit the message when the source bot replies.
        await callback_query.answer("So'rov yuborildi. Kuting...")
    else:
        await callback_query.answer("❌ Amaliyotni bajarishda xatolik yuz berdi yoki raqam muddati tugagan.", show_alert=True)

async def info_handler(callback_query: types.CallbackQuery):
    await callback_query.message.answer("Bu bot orqali manba botdan raqam olib, premium qilishingiz mumkin.")
    await callback_query.answer()

async def help_message_handler(message: types.Message):
    await message.answer("📞 Yordamchi bo'limiga xush kelibsiz.\n\nSavollaringiz bo'lsa yoki yordam kerak bo'lsa adminga murojaat qiling.")

def register_user_handlers(dp: Dispatcher):
    dp.message.register(start_command, Command("start"))
    dp.message.register(get_number_command, Command("getNumber"))
    dp.message.register(help_message_handler, F.text == "Yordamchi")

    dp.callback_query.register(stats_handler, F.data == "user:stats")
    dp.callback_query.register(help_handler, F.data == "user:help")
    dp.callback_query.register(withdraw_handler, F.data == "user:withdraw")
    dp.callback_query.register(cards_handler, F.data == "user:cards")

    dp.callback_query.register(get_number_handler, F.data == "user:get_number")
    dp.callback_query.register(info_handler, F.data == "user:info")
    dp.callback_query.register(source_button_callback, F.data.startswith("source_btn:"))
