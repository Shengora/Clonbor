from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
import asyncio

from bot.database import db
from bot.core.config import ADMIN_IDS
from bot.keyboards.inline import get_admin_panel_keyboard, get_accounts_keyboard

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

async def admin_callback(callback_query: types.CallbackQuery):
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
        # Simply instructing user to run a python script to add sessions into SQLite directly for security
        await callback_query.message.answer("Yangi akkaunt qo'shish uchun serverda `python3 add_session.py <phone_number>` komandasini ishlating va kodni kiriting.")
        await callback_query.answer()
    elif action == "accounts":
        accounts = await db.get_all_accounts()
        await callback_query.message.edit_text(
            "Mavjud akkauntlar (Userbotlar):",
            reply_markup=get_accounts_keyboard(accounts)
        )

    elif action == "statistics":
        today_stat = await db.get_today_statistics()
        today_premium = today_stat['premium_count'] if today_stat else 0
        today_spent = today_stat['total_spent'] if today_stat else 0
        total_premium = await db.get_total_premium_count()
        total_balance = await db.get_total_balance()

        stat_text = (
            f"📊 Statistika\n\n"
            f"Bugungi premiumlar: {today_premium}\n"
            f"Bugun to'langan: {today_spent} so'm\n\n"
            f"Umumiy premiumlar: {total_premium}\n"
            f"Foydalanuvchilardagi umumiy balans: {total_balance} so'm"
        )
        await callback_query.answer(stat_text, show_alert=True)

    elif action == "toggle_number_status":
        current_status = await db.get_setting("number_status")
        new_status = "0" if current_status == "1" else "1"
        await db.set_setting("number_status", new_status)
        status_text = "Yoqilgan" if new_status == "1" else "O'chirilgan"
        await callback_query.answer(f"Nomer berish statusi: {status_text}", show_alert=True)

    elif action == "user_price":
        current_price = await db.get_setting("user_price")
        await callback_query.message.answer(f"Joriy user narxi: {current_price} so'm.\nO'zgartirish uchun hali alohida state yozilmagan (simulyatsiya).")
        await callback_query.answer()

    else:
        await callback_query.answer("Bu bo'lim hali to'liq ishga tushirilmagan.", show_alert=True)

def register_admin_handlers(dp: Dispatcher):
    dp.message.register(admin_command, Command("admin"))
    dp.callback_query.register(admin_callback, F.data.startswith("admin:"))
