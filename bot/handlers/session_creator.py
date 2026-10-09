from __future__ import annotations
from pyrogram import Client
from pyrogram.errors import SessionPasswordNeeded, PhoneCodeInvalid, PhoneCodeExpired
from aiogram import types, Dispatcher, F
from aiogram.fsm.context import FSMContext
from bot.handlers.fsm import AdminStates
from bot.database import db
from bot.core.config import API_ID, API_HASH
from bot.handlers.admin import is_admin
import logging

logger = logging.getLogger(__name__)

# Temporary in-memory storage for active Pyrogram clients during login
login_clients = {}

async def ask_phone_number(callback_query: types.CallbackQuery, state: FSMContext):
    if not await is_admin(callback_query.from_user.id):
        return
    await callback_query.message.answer("Yangi akkaunt qo'shish uchun telefon raqamni kiriting (masalan: +998901234567):")
    await state.set_state(AdminStates.waiting_for_phone)
    await callback_query.answer()

async def process_phone_number(message: types.Message, state: FSMContext):
    if not await is_admin(message.from_user.id):
        return

    phone_number = message.text.strip()

    await message.answer("⏳ Kod so'ralmoqda, kuting...")

    # Initialize an in-memory client
    client = Client(name=f"temp_{message.from_user.id}", api_id=API_ID, api_hash=API_HASH, in_memory=True)
    await client.connect()

    try:
        sent_code = await client.send_code(phone_number)

        login_clients[message.from_user.id] = {
            "client": client,
            "phone_number": phone_number,
            "phone_code_hash": sent_code.phone_code_hash
        }

        await message.answer(f"✅ {phone_number} raqamiga kod yuborildi.\nIltimos, Telegramdan kelgan kodni kiriting:")
        await state.set_state(AdminStates.waiting_for_code)
    except Exception as e:
        await message.answer(f"❌ Kod yuborishda xatolik yuz berdi:\n`{e}`")
        await client.disconnect()
        await state.clear()

async def process_code(message: types.Message, state: FSMContext):
    if not await is_admin(message.from_user.id):
        return

    code = message.text.strip()
    user_data = login_clients.get(message.from_user.id)

    if not user_data:
        await message.answer("❌ Seans topilmadi. Iltimos, boshqattan urinib ko'ring.")
        await state.clear()
        return

    client: Client = user_data["client"]
    phone_number = user_data["phone_number"]
    phone_code_hash = user_data["phone_code_hash"]

    try:
        await client.sign_in(phone_number, phone_code_hash, code)

        # Successfully signed in
        session_string = await client.export_session_string()
        account_id = await db.add_account(phone_number, session_string)

        await client.disconnect()
        del login_clients[message.from_user.id]

        from bot.core.userbot import userbot_manager
        await userbot_manager.start_account(account_id, session_string)

        await message.answer("✅ Akkaunt muvaffaqiyatli saqlandi va avtomatik ishga tushirildi! Endi raqam olish mumkin.")
        await state.clear()

    except SessionPasswordNeeded:
        await message.answer("🔐 Bu akkauntda 2FA parol yoqilgan. Iltimos, parolni kiriting:")
        await state.set_state(AdminStates.waiting_for_password)
    except (PhoneCodeInvalid, PhoneCodeExpired) as e:
        await message.answer(f"❌ Kod xato yoki muddati tugagan. Boshqatdan urinib ko'ring: `{e}`")
        await client.disconnect()
        del login_clients[message.from_user.id]
        await state.clear()
    except Exception as e:
        await message.answer(f"❌ Noma'lum xatolik yuz berdi: `{e}`")
        await client.disconnect()
        del login_clients[message.from_user.id]
        await state.clear()

async def process_password(message: types.Message, state: FSMContext):
    if not await is_admin(message.from_user.id):
        return

    password = message.text.strip()
    user_data = login_clients.get(message.from_user.id)

    if not user_data:
        await message.answer("❌ Seans topilmadi. Iltimos, boshqattan urinib ko'ring.")
        await state.clear()
        return

    client: Client = user_data["client"]
    phone_number = user_data["phone_number"]

    try:
        await client.check_password(password)

        session_string = await client.export_session_string()
        account_id = await db.add_account(phone_number, session_string)

        await client.disconnect()
        del login_clients[message.from_user.id]

        from bot.core.userbot import userbot_manager
        await userbot_manager.start_account(account_id, session_string)

        await message.answer("✅ Akkaunt muvaffaqiyatli saqlandi va avtomatik ishga tushirildi! Endi raqam olish mumkin.")
        await state.clear()

    except Exception as e:
        await message.answer(f"❌ Parol xato yoki xatolik yuz berdi: `{e}`")
        await client.disconnect()
        del login_clients[message.from_user.id]
        await state.clear()

def register_session_handlers(dp: Dispatcher):
    dp.message.register(process_phone_number, AdminStates.waiting_for_phone)
    dp.message.register(process_code, AdminStates.waiting_for_code)
    dp.message.register(process_password, AdminStates.waiting_for_password)
