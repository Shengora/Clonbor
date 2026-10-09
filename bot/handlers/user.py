from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import asyncio

from bot.database import db
from bot.core.userbot import userbot_manager

def get_main_keyboard():
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔵 My Stats", callback_data="user:stats")],
            [InlineKeyboardButton(text="🟢 Yordamchi", callback_data="user:help")],
            [InlineKeyboardButton(text="🟢 Pul yechish", callback_data="user:withdraw")],
            [InlineKeyboardButton(text="🔵 Mening kartalarim", callback_data="user:cards")]
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

async def check_channels(user_id: int, bot: Bot) -> bool:
    channels_str = await db.get_setting("channels")
    if not channels_str:
        return True

    channels = [c.strip() for c in channels_str.split(",") if c.strip()]
    for channel in channels:
        try:
            member = await bot.get_chat_member(chat_id=channel, user_id=user_id)
            if member.status in ['left', 'kicked']:
                return False
        except Exception:
            # If bot is not admin in channel, we just assume false or ignore.
            return False
    return True

async def start_command(message: types.Message, bot: Bot):
    # Oldin bazada bormi yo'qligini tekshiramiz
    user = await db.get_user(message.from_user.id)
    is_new = user is None

    await db.add_user(
        message.from_user.id,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name,
        username=message.from_user.username
    )

    if is_new:
        await message.answer("⏳ Ariza yuborildi. Administrator tasdig'i kutilmoqda...")

        # Adminga yuborish
        from bot.core.config import ADMIN_IDS
        admin_markup = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"admin:approve_user:{message.from_user.id}")],
            [InlineKeyboardButton(text="❌ Bloklash", callback_data=f"admin:block_user:{message.from_user.id}")]
        ])

        username = f"@{message.from_user.username}" if message.from_user.username else "Yo'q"

        for admin_id in ADMIN_IDS:
            try:
                await bot.send_message(
                    admin_id,
                    f"👤 Yangi foydalanuvchi botga kirdi:\nID: {message.from_user.id}\nIsmi: {message.from_user.first_name}\nUsername: {username}",
                    reply_markup=admin_markup
                )
            except Exception:
                pass
        return

    user = await db.get_user(message.from_user.id)
    if user and user['state'] == 'pending':
        await message.answer("⏳ Administrator tasdig'i kutilmoqda...")
        return

    if user and user['state'] == 'blocked':
        await message.answer("❌ Siz bloklangansiz.")
        return

    if not await check_channels(message.from_user.id, bot):
        channels_str = await db.get_setting("channels")
        await message.answer(f"Iltimos, botdan foydalanish uchun quyidagi kanallarga obuna bo'ling:\n{channels_str}")
        return

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

from aiogram.fsm.context import FSMContext
from bot.handlers.fsm import UserStates
from bot.core.config import ADMIN_IDS

async def withdraw_handler(callback_query: types.CallbackQuery, state: FSMContext):
    user = await db.get_user(callback_query.from_user.id)
    if not user:
        await callback_query.answer("Siz ro'yxatdan o'tmagansiz.", show_alert=True)
        return

    if user['balance'] < 15000:
        await callback_query.answer(f"❌ Pul yechish uchun hisobingizda kamida 15000 so'm bo'lishi kerak.\nSizda: {user['balance']} so'm", show_alert=True)
        return

    if not user['wallet']:
        await callback_query.answer("❌ Avval 'Mening kartalarim' bo'limidan karta yoki hamyon kiriting!", show_alert=True)
        return

    await callback_query.message.answer(
        f"💸 Qancha pul yechmoqchisiz?\n"
        f"Sizning balansingiz: {user['balance']} so'm\n"
        f"Karta raqamingiz: {user['wallet']}\n\n"
        f"Miqdorni raqamlarda kiriting:"
    )
    await state.set_state(UserStates.waiting_for_withdraw_amount)
    await callback_query.answer()

async def process_withdraw_amount(message: types.Message, state: FSMContext):
    try:
        amount = int(message.text.strip())
    except ValueError:
        await message.answer("❌ Iltimos, miqdorni faqat raqamlarda kiriting.")
        return

    user = await db.get_user(message.from_user.id)
    if amount < 15000:
        await message.answer("❌ Minimal pul yechish miqdori 15000 so'm.")
        return

    if amount > user['balance']:
        await message.answer(f"❌ Hisobingizda yetarli mablag' yo'q. Maksimal yechish: {user['balance']} so'm.")
        return

    # Deduct balance and send to admin
    await db.update_user_balance(message.from_user.id, -amount)
    await message.answer("✅ Pul yechish so'rovingiz adminga yuborildi. Tez orada kartangizga tushirib beriladi.")

    from bot.core.forwarder import forwarder
    if forwarder.bot:
        for admin_id in ADMIN_IDS:
            try:
                await forwarder.bot.send_message(
                    admin_id,
                    f"💸 <b>Yangi pul yechish so'rovi!</b>\n\n"
                    f"👤 User ID: <code>{message.from_user.id}</code>\n"
                    f"💳 Karta/Hamyon: <code>{user['wallet']}</code>\n"
                    f"💰 Miqdor: <b>{amount} so'm</b>",
                    parse_mode="HTML"
                )
            except Exception:
                pass

    await state.clear()


async def cards_handler(callback_query: types.CallbackQuery, state: FSMContext):
    user = await db.get_user(callback_query.from_user.id)
    if not user:
        await callback_query.answer("Siz ro'yxatdan o'tmagansiz.", show_alert=True)
        return

    current_wallet = user['wallet'] if user['wallet'] else "Yo'q"

    await callback_query.message.answer(
        f"💳 Hozirgi saqlangan karta/hamyon: {current_wallet}\n\n"
        f"Yangi karta yoki crypto hamyon raqamini yuboring:"
    )
    await state.set_state(UserStates.waiting_for_wallet)
    await callback_query.answer()

async def process_wallet(message: types.Message, state: FSMContext):
    wallet = message.text.strip()
    await db.update_user_wallet(message.from_user.id, wallet)
    await message.answer(f"✅ Karta / Hamyon raqami saqlandi: {wallet}")
    await state.clear()

import hashlib

# Memory mapping to avoid 64-byte callback_data limits in Telegram API
callback_data_store = {}

def create_inline_keyboard_from_source(source_markup) -> InlineKeyboardMarkup | None:
    if not source_markup or not source_markup.inline_keyboard:
        return None

    inline_keyboard = []
    for row in source_markup.inline_keyboard:
        new_row = []
        for button in row:
            # We map source button text to our callback data
            # Hash it to prevent ButtonDataInvalid (Telegram 64 byte limit)
            btn_hash = hashlib.md5(button.text.encode()).hexdigest()[:16]
            callback_data_store[btn_hash] = button.text

            callback_data = f"src_btn:{btn_hash}"
            new_row.append(InlineKeyboardButton(text=button.text, callback_data=callback_data))
        inline_keyboard.append(new_row)

    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)

async def can_request_number(user_id: int) -> tuple[bool, str]:
    user = await db.get_user(user_id)
    if not user or user['state'] == 'pending':
        return False, "⏳ Administrator tasdig'i kutilmoqda..."
    if user and user['state'] == 'blocked':
        return False, "❌ Siz bloklangansiz va raqam ololmaysiz."

    number_status = await db.get_setting("number_status")
    if number_status == "0":
        return False, "❌ Hozircha raqam berish vaqtincha to'xtatilgan."

    slot_limit_str = await db.get_setting("slot_limit")
    if slot_limit_str:
        slot_limit = int(slot_limit_str)
        # Check if the user has requested more than their limit (based on successful premiums)
        if user and user['premium_count'] >= slot_limit:
            # Whitelisted users bypass the slot limit
            if user['state'] != 'whitelist':
                return False, f"❌ Siz kunlik/umumiy raqam olish limitiga yetib keldingiz (Limit: {slot_limit})."

    return True, ""

import re

import html

async def _log_number_to_channel(bot: Bot, user_id: int, user_info: str, response_text: str):
    log_channel = await db.get_setting("log_channel")
    if not log_channel:
        return

    try:
        # Simple extraction of the phone number from the text if it contains one (most likely starts with +)
        match = re.search(r'\+?\d{7,15}', response_text)
        number_str = match.group(0) if match else "Noma'lum raqam"
        safe_user_info = html.escape(user_info)

        log_text = (
            f"🟢 <b>Yangi raqam olindi!</b>\n\n"
            f"👤 <b>Foydalanuvchi:</b> {safe_user_info}\n"
            f"🆔 <b>ID:</b> <code>{user_id}</code>\n"
            f"📞 <b>Raqam:</b> <code>{number_str}</code>\n"
        )

        await bot.send_message(chat_id=log_channel, text=log_text, parse_mode="HTML")
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Failed to log number to channel: {e}")

async def get_number_command(message: types.Message, bot: Bot):
    if not await check_channels(message.from_user.id, bot):
        channels_str = await db.get_setting("channels")
        await message.answer(f"Iltimos, avval quyidagi kanallarga obuna bo'ling:\n{channels_str}")
        return

    allowed, err_msg = await can_request_number(message.from_user.id)
    if not allowed:
        await message.answer(err_msg)
        return

    msg = await message.answer("⏳ Raqam olinmoqda, kuting...")

    response = await userbot_manager.request_number(message.from_user.id, msg.message_id)

    if response:
        response_text = response.get("text", "Raqam ma'lumotlari:")
        keyboard = create_inline_keyboard_from_source(response.get("reply_markup"))
        await msg.edit_text(response_text, reply_markup=keyboard)

        uname = f"@{message.from_user.username}" if message.from_user.username else message.from_user.first_name
        await _log_number_to_channel(bot, message.from_user.id, uname, response_text)
    else:
        await msg.edit_text("❌ Hozircha bo'sh raqamlar yo'q yoki manba bilan bog'lanishda xatolik yuz berdi.")

async def get_number_handler(callback_query: types.CallbackQuery, bot: Bot):
    if not await check_channels(callback_query.from_user.id, bot):
        await callback_query.answer("Iltimos, avval kanallarga obuna bo'ling!", show_alert=True)
        return

    allowed, err_msg = await can_request_number(callback_query.from_user.id)
    if not allowed:
        await callback_query.answer(err_msg, show_alert=True)
        return

    msg = await callback_query.message.answer("⏳ Raqam olinmoqda, kuting...")
    await callback_query.answer()

    response = await userbot_manager.request_number(callback_query.from_user.id, msg.message_id)

    if response:
        response_text = response.get("text", "Raqam ma'lumotlari:")
        keyboard = create_inline_keyboard_from_source(response.get("reply_markup"))
        await msg.edit_text(response_text, reply_markup=keyboard)

        uname = f"@{callback_query.from_user.username}" if callback_query.from_user.username else callback_query.from_user.first_name
        await _log_number_to_channel(bot, callback_query.from_user.id, uname, response_text)
    else:
        await msg.edit_text("❌ Hozircha bo'sh raqamlar yo'q yoki manba bilan bog'lanishda xatolik yuz berdi.")

async def handle_premium_stats(user_telegram_id: int, source_message_id: int, text: str):
    lower_text = text.lower()

    if "premium activated and counted" in lower_text:
        # Prevent double-spending
        if await db.is_message_processed(source_message_id):
            return
        await db.mark_message_processed(source_message_id)

        user = await db.get_user(user_telegram_id)
        if user and user['custom_price'] is not None:
            user_price = user['custom_price']
        else:
            user_price_str = await db.get_setting('user_price')
            user_price = int(user_price_str) if user_price_str else 5000

        await db.update_user_balance(user_telegram_id, user_price)
        await db.increment_user_premium_count(user_telegram_id)
        await db.update_statistics(user_price)

        from bot.core.forwarder import forwarder
        if forwarder.bot:
            await forwarder.bot.send_message(user_telegram_id, f"🎉 Tabriklaymiz! Premium muvaffaqiyatli faollashtirildi.\n💰 Balansingizga {user_price} so'm qo'shildi.")

    elif "cancel" in lower_text or "bekor qilindi" in lower_text:
        if not await db.is_message_processed(source_message_id):
            await db.mark_message_processed(source_message_id)
            await db.increment_user_canceled_numbers(user_telegram_id)

    elif "frozen" in lower_text or "muzlatildi" in lower_text:
        if not await db.is_message_processed(source_message_id):
            await db.mark_message_processed(source_message_id)
            await db.increment_user_frozen_numbers(user_telegram_id)

    elif "code" in lower_text or "kod:" in lower_text:
        # We don't mark 'code' as fully processed because it might be followed by 'premium activated' later on the same message
        await db.increment_user_codes_received(user_telegram_id)

async def source_button_callback(callback_query: types.CallbackQuery):
    btn_hash = callback_query.data.split(":", 1)[1]
    button_text = callback_data_store.get(btn_hash)

    if not button_text:
        await callback_query.answer("❌ Tugma muddati tugagan.", show_alert=True)
        return

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

    dp.message.register(process_wallet, UserStates.waiting_for_wallet)
    dp.message.register(process_withdraw_amount, UserStates.waiting_for_withdraw_amount)

    dp.callback_query.register(stats_handler, F.data == "user:stats")
    dp.callback_query.register(help_handler, F.data == "user:help")
    dp.callback_query.register(withdraw_handler, F.data == "user:withdraw")
    dp.callback_query.register(cards_handler, F.data == "user:cards")

    dp.callback_query.register(get_number_handler, F.data == "user:get_number")
    dp.callback_query.register(info_handler, F.data == "user:info")
    dp.callback_query.register(source_button_callback, F.data.startswith("src_btn:"))
