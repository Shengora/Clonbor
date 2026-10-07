from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
import asyncio

from bot.database import db
from bot.core.config import ADMIN_IDS
from bot.keyboards.inline import get_admin_panel_keyboard, get_accounts_keyboard, get_sources_keyboard, get_back_to_main_keyboard
from bot.handlers.fsm import AdminStates

async def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

async def admin_command(message: types.Message):
    if not await is_admin(message.from_user.id):
        return

    total_users = await db.get_total_users_count()
    total_premium = await db.get_total_premium_count()
    slot_limit = await db.get_setting("slot_limit")

    text = (
        f"👑 Admin Panel\n\n"
        f"👥 Jami obunachilar: {total_users}\n"
        f"⭐ Jami premium: {total_premium}\n"
        f"🆔 Slot limit: {slot_limit}"
    )

    await message.answer(text, reply_markup=get_admin_panel_keyboard())

async def admin_callback(callback_query: types.CallbackQuery, state: FSMContext):
    if not await is_admin(callback_query.from_user.id):
        return

    action = callback_query.data.split(":")[1]

    if action == "main":
        total_users = await db.get_total_users_count()
        total_premium = await db.get_total_premium_count()
        slot_limit = await db.get_setting("slot_limit")
        text = (
            f"👑 Admin Panel\n\n"
            f"👥 Jami obunachilar: {total_users}\n"
            f"⭐ Jami premium: {total_premium}\n"
            f"🆔 Slot limit: {slot_limit}"
        )
        await callback_query.message.edit_text(text, reply_markup=get_admin_panel_keyboard())

    elif action == "add_account":
        from bot.handlers.session_creator import ask_phone_number
        await ask_phone_number(callback_query, state)

    elif action == "accounts":
        accounts = await db.get_all_accounts()
        await callback_query.message.edit_text(
            "Mavjud akkauntlar (Userbotlar):",
            reply_markup=get_accounts_keyboard(accounts)
        )

    elif action == "statistics":
        # Fetch individual users stats
        users_stats = await db.get_all_users_stats(limit=50) # top 50

        if not users_stats:
            await callback_query.message.edit_text("Hali ro'yxatda foydalanuvchilar yo'q.", reply_markup=get_back_to_main_keyboard())
            return

        stat_text = "📊 <b>Foydalanuvchilar Statistikasi (Top 50)</b>\n\n"

        for i, u in enumerate(users_stats, 1):
            stat_text += (
                f"👤 <b>{i}. ID:</b> <code>{u['telegram_id']}</code>\n"
                f"   ⭐ Premium: {u['premium_count']} | 🧊 Muzlatilgan: {u['frozen_numbers']} | ❌ Bekor: {u['canceled_numbers']}\n\n"
            )

        await callback_query.message.edit_text(stat_text, reply_markup=get_back_to_main_keyboard(), parse_mode="HTML")

    elif action == "broadcast":
        await callback_query.message.answer("📣 Barcha foydalanuvchilarga yuboriladigan xabarni kiriting (yoki Bekor qilish tugmasini bosing):")
        await state.set_state(AdminStates.waiting_for_broadcast_msg)
        await callback_query.answer()

    elif action == "change_balance":
        await callback_query.message.answer("Hisobini o'zgartirmoqchi bo'lgan foydalanuvchining ID raqamini kiriting:")
        await state.set_state(AdminStates.waiting_for_balance_user_id)
        await callback_query.answer()

    elif action == "user_price":
        current_price = await db.get_setting("user_price")
        await callback_query.message.answer(f"Joriy user narxi: {current_price} so'm.\nYangi narxni kiriting:")
        await state.update_data(setting_key="user_price")
        await state.set_state(AdminStates.waiting_for_setting_value)
        await callback_query.answer()

    elif action == "slot_limit":
        current_limit = await db.get_setting("slot_limit")
        await callback_query.message.answer(f"Joriy Slot Limit: {current_limit}.\nYangi limitni kiriting:")
        await state.update_data(setting_key="slot_limit")
        await state.set_state(AdminStates.waiting_for_setting_value)
        await callback_query.answer()

    elif action == "toggle_number_status":
        current_status = await db.get_setting("number_status")
        new_status = "0" if current_status == "1" else "1"
        await db.set_setting("number_status", new_status)
        status_text = "Yoqilgan" if new_status == "1" else "O'chirilgan"
        await callback_query.answer(f"Nomer berish statusi: {status_text}", show_alert=True)

    elif action == "sources":
        await callback_query.message.edit_text(
            "Manbalar (Source bots) bo'limi:",
            reply_markup=get_sources_keyboard()
        )

    elif action == "source_info":
        current_source = await db.get_setting("source_bot")
        await callback_query.answer(f"Joriy manba bot: {current_source}", show_alert=True)

    elif action == "source_change":
        await callback_query.message.answer("Yangi manba bot usernamesini kiriting (masalan: @yangi_bot):")
        await state.set_state(AdminStates.waiting_for_new_source)
        await callback_query.answer()

    else:
        await callback_query.answer("Bu bo'lim hali to'liq ishga tushirilmagan.", show_alert=True)

async def set_new_source_bot(message: types.Message, state: FSMContext):
    if not await is_admin(message.from_user.id):
        return

    new_source = message.text.strip()
    if not new_source.startswith("@"):
        await message.answer("Xato! Username @ bilan boshlanishi kerak.")
        return

    await db.set_setting("source_bot", new_source)
    await message.answer(f"Manba bot muvaffaqiyatli o'zgartirildi: {new_source}\nIltimos botni restart qiling, yangi filter ishlashi uchun.")
    await state.clear()

async def process_broadcast(message: types.Message, state: FSMContext):
    if not await is_admin(message.from_user.id):
        return

    users = await db.get_all_users()
    count = 0
    await message.answer("Yuborilmoqda...")
    for u in users:
        try:
            await message.send_copy(chat_id=u['telegram_id'])
            count += 1
            await asyncio.sleep(0.05) # spam limit
        except Exception:
            pass

    await message.answer(f"✅ Xabar {count} ta foydalanuvchiga muvaffaqiyatli yuborildi.")
    await state.clear()

async def process_balance_user_id(message: types.Message, state: FSMContext):
    if not await is_admin(message.from_user.id):
        return

    try:
        target_id = int(message.text.strip())
        user = await db.get_user(target_id)
        if not user:
            await message.answer("❌ Bunday foydalanuvchi topilmadi.")
            await state.clear()
            return

        await state.update_data(target_id=target_id, current_balance=user['balance'])
        await message.answer(f"Foydalanuvchi balansi: {user['balance']} so'm\n\nQo'shish uchun musbat son (masalan: 10000) yoki ayirish uchun manfiy son (masalan: -5000) kiriting:")
        await state.set_state(AdminStates.waiting_for_balance_amount)
    except ValueError:
        await message.answer("❌ ID raqamdan iborat bo'lishi kerak.")

async def process_balance_amount(message: types.Message, state: FSMContext):
    if not await is_admin(message.from_user.id):
        return

    try:
        amount = int(message.text.strip())
        data = await state.get_data()
        target_id = data.get("target_id")

        await db.update_user_balance(target_id, amount)
        new_user = await db.get_user(target_id)

        await message.answer(f"✅ Balans o'zgartirildi!\nYangi balans: {new_user['balance']} so'm.")
        await state.clear()
    except ValueError:
        await message.answer("❌ Summa raqamdan iborat bo'lishi kerak.")

async def process_setting_value(message: types.Message, state: FSMContext):
    if not await is_admin(message.from_user.id):
        return

    value = message.text.strip()
    data = await state.get_data()
    setting_key = data.get("setting_key")

    await db.set_setting(setting_key, value)
    await message.answer(f"✅ Sozlama muvaffaqiyatli yangilandi: {setting_key} = {value}")
    await state.clear()

def register_admin_handlers(dp: Dispatcher):
    dp.message.register(admin_command, Command("admin"))
    dp.callback_query.register(admin_callback, F.data.startswith("admin:"))
    dp.message.register(set_new_source_bot, AdminStates.waiting_for_new_source)
    dp.message.register(process_broadcast, AdminStates.waiting_for_broadcast_msg)
    dp.message.register(process_balance_user_id, AdminStates.waiting_for_balance_user_id)
    dp.message.register(process_balance_amount, AdminStates.waiting_for_balance_amount)
    dp.message.register(process_setting_value, AdminStates.waiting_for_setting_value)
