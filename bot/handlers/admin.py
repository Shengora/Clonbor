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

    action = callback_query.data.split(":", 1)[1]

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

    elif action.startswith("acc:"):
        account_id = int(action.split(":")[1])
        # Currently, just give an option to delete it
        await db.delete_account(account_id)
        from bot.core.userbot import userbot_manager
        await userbot_manager.stop_account(account_id)
        await callback_query.answer("Akkaunt o'chirildi va to'xtatildi.", show_alert=True)
        # Refresh accounts list
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
            uname = f" (@{u['username']})" if u['username'] else ""
            stat_text += (
                f"👤 <b>{i}. ID:</b> <code>{u['telegram_id']}</code>{uname}\n"
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
        await show_user_prices_page(callback_query.message, 0)
        await callback_query.answer()

    elif action.startswith("user_price_page:"):
        page = int(action.split(":")[1])
        await show_user_prices_page(callback_query.message, page, edit=True)
        await callback_query.answer()

    elif action == "global_price_set":
        current_price = await db.get_setting("user_price")
        await callback_query.message.answer(f"Joriy umumiy narx: {current_price} so'm.\nYangi umumiy narxni kiriting:")
        await state.update_data(setting_key="user_price")
        await state.set_state(AdminStates.waiting_for_setting_value)
        await callback_query.answer()

    elif action.startswith("set_user_price:"):
        target_user_id = int(action.split(":")[1])
        await state.update_data(custom_price_user_id=target_user_id)
        await callback_query.message.answer("Ushbu foydalanuvchi uchun maxsus narxni kiriting (yoki '0' yozing umumiy narxga o'tkazish uchun):")
        await state.set_state(AdminStates.waiting_for_custom_price)
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

    elif action == "channels":
        current_channels = await db.get_setting("channels")
        text = f"Hozirgi kanallar:\n{current_channels}\n\nYangi kanallarni vergul bilan ajratib yozing (masalan: @kanal1, @kanal2). O'chirish uchun '0' yozing:"
        await callback_query.message.answer(text)
        await state.set_state(AdminStates.waiting_for_channel)
        await callback_query.answer()

    elif action == "log_channel":
        current_log_channel = await db.get_setting("log_channel")
        text = f"Hozirgi log kanal: {current_log_channel}\n\nYangi log kanal usernamesini yoki IDsini kiriting (masalan: @logkanal). O'chirish uchun '0' yozing:"
        await callback_query.message.answer(text)
        await state.set_state(AdminStates.waiting_for_log_channel)
        await callback_query.answer()

    elif action == "whitelist":
        await callback_query.message.answer("Whitelistga qo'shish yoki olib tashlash uchun foydalanuvchi ID sini kiriting:")
        await state.set_state(AdminStates.waiting_for_whitelist)
        await callback_query.answer()

    elif action == "blocklist":
        await callback_query.message.answer("Bloklash yoki blokdan chiqarish uchun foydalanuvchi ID sini kiriting:")
        await state.set_state(AdminStates.waiting_for_blocklist)
        await callback_query.answer()

    elif action == "unstable_numbers":
        await callback_query.message.answer("Beqaror raqamlar ro'yxati hozircha mavjud emas. (Loglarni tekshiring)")
        await callback_query.answer()

    elif action == "download_stat":
        users_stats = await db.get_all_users_stats(limit=99999)
        if not users_stats:
            await callback_query.answer("Ma'lumotlar yo'q.", show_alert=True)
            return

        csv_text = "TelegramID,Premium,Frozen,Canceled\n"
        for u in users_stats:
            csv_text += f"{u['telegram_id']},{u['premium_count']},{u['frozen_numbers']},{u['canceled_numbers']}\n"

        from aiogram.types import BufferedInputFile
        file = BufferedInputFile(csv_text.encode('utf-8'), filename="users_stats.csv")
        await callback_query.message.answer_document(document=file, caption="Foydalanuvchilar statistikasi")
        await callback_query.answer()

    elif action == "resetall":
        await db.reset_all_statistics()
        await callback_query.answer("Barcha statistika muvaffaqiyatli 0 ga tushirildi!", show_alert=True)
        # Bosh sahifaga qaytamiz
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

    elif action == "delete_messages":
        await callback_query.message.delete()
        await callback_query.answer("Bosh menyu xabari o'chirildi.")

    # Yangi foydalanuvchini tasdiqlash tugmalari
    elif action.startswith("approve_user:"):
        user_id = int(action.split(":")[1])
        import aiosqlite
        async with aiosqlite.connect(db.DB_PATH) as database:
            await database.execute('UPDATE users SET state = ? WHERE telegram_id = ?', ('active', user_id))
            await database.commit()
        await callback_query.answer("Foydalanuvchi tasdiqlandi!", show_alert=True)
        from bot.core.forwarder import forwarder
        if forwarder.bot:
            try:
                await forwarder.bot.send_message(user_id, "✅ Sizning arizangiz admin tomonidan tasdiqlandi! Endi botdan to'liq foydalanishingiz mumkin. /start ni bosing.")
            except Exception:
                pass
        await callback_query.message.delete()

    elif action.startswith("block_user:"):
        user_id = int(action.split(":")[1])
        import aiosqlite
        async with aiosqlite.connect(db.DB_PATH) as database:
            await database.execute('UPDATE users SET state = ? WHERE telegram_id = ?', ('blocked', user_id))
            await database.commit()
        await callback_query.answer("Foydalanuvchi bloklandi!", show_alert=True)
        from bot.core.forwarder import forwarder
        if forwarder.bot:
            try:
                await forwarder.bot.send_message(user_id, "❌ Kechirasiz, sizning botdan foydalanish arizangiz admin tomonidan rad etildi.")
            except Exception:
                pass
        await callback_query.message.delete()

    else:
        await callback_query.answer("Kechirasiz, xatolik yuz berdi.", show_alert=True)

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

async def process_channel(message: types.Message, state: FSMContext):
    if not await is_admin(message.from_user.id):
        return

    value = message.text.strip()
    if value == '0':
        await db.set_setting("channels", "")
        await message.answer("✅ Majburiy kanallar o'chirildi.")
    else:
        await db.set_setting("channels", value)
        await message.answer(f"✅ Majburiy kanallar o'rnatildi: {value}")
    await state.clear()

async def process_log_channel(message: types.Message, state: FSMContext):
    if not await is_admin(message.from_user.id):
        return

    value = message.text.strip()
    if value == '0':
        await db.set_setting("log_channel", "")
        await message.answer("✅ Log kanal o'chirildi.")
    else:
        await db.set_setting("log_channel", value)
        await message.answer(f"✅ Log kanal o'rnatildi: {value}")
    await state.clear()

async def process_whitelist(message: types.Message, state: FSMContext):
    if not await is_admin(message.from_user.id):
        return

    try:
        target_id = int(message.text.strip())
        user = await db.get_user(target_id)
        if not user:
            await message.answer("❌ Bunday foydalanuvchi topilmadi.")
        else:
            new_state = 'active' if user['state'] == 'whitelist' else 'whitelist'
            import aiosqlite
            async with aiosqlite.connect(db.DB_PATH) as database:
                await database.execute('UPDATE users SET state = ? WHERE telegram_id = ?', (new_state, target_id))
                await database.commit()
            await message.answer(f"✅ Foydalanuvchi ({target_id}) statusi '{new_state}' qilib o'zgartirildi.")
    except Exception as e:
        await message.answer("❌ Xatolik yuz berdi. ID raqam kiriting.")
    await state.clear()

async def process_blocklist(message: types.Message, state: FSMContext):
    if not await is_admin(message.from_user.id):
        return

    try:
        target_id = int(message.text.strip())
        user = await db.get_user(target_id)
        if not user:
            await message.answer("❌ Bunday foydalanuvchi topilmadi.")
        else:
            new_state = 'active' if user['state'] == 'blocked' else 'blocked'
            import aiosqlite
            async with aiosqlite.connect(db.DB_PATH) as database:
                await database.execute('UPDATE users SET state = ? WHERE telegram_id = ?', (new_state, target_id))
                await database.commit()
            await message.answer(f"✅ Foydalanuvchi ({target_id}) statusi '{new_state}' qilib o'zgartirildi.")
    except Exception as e:
        await message.answer("❌ Xatolik yuz berdi. ID raqam kiriting.")
    await state.clear()


from bot.keyboards.inline import get_users_price_keyboard

async def show_user_prices_page(message: types.Message, page: int, edit: bool = False):
    users = await db.get_all_users()
    per_page = 10
    total_pages = (len(users) + per_page - 1) // per_page

    if total_pages == 0:
        total_pages = 1

    start_idx = page * per_page
    end_idx = start_idx + per_page
    page_users = users[start_idx:end_idx]

    keyboard = get_users_price_keyboard(page_users, page, total_pages)
    text = f"👤 Foydalanuvchilar narxlari (Sahifa: {page + 1}/{total_pages})"

    if edit:
        await message.edit_text(text, reply_markup=keyboard)
    else:
        await message.answer(text, reply_markup=keyboard)

async def process_custom_price(message: types.Message, state: FSMContext):
    if not await is_admin(message.from_user.id):
        return

    try:
        price = int(message.text.strip())
        data = await state.get_data()
        target_id = data.get("custom_price_user_id")

        db_price = price if price > 0 else None

        import aiosqlite
        async with aiosqlite.connect(db.DB_PATH) as database:
            await database.execute('UPDATE users SET custom_price = ? WHERE telegram_id = ?', (db_price, target_id))
            await database.commit()

        await message.answer("✅ Foydalanuvchi narxi muvaffaqiyatli o'zgartirildi.")
        await state.clear()

        await show_user_prices_page(message, 0)
    except ValueError:
        await message.answer("❌ Narx raqamdan iborat bo'lishi kerak.")

def register_admin_handlers(dp: Dispatcher):
    dp.message.register(admin_command, Command("admin"))
    dp.callback_query.register(admin_callback, F.data.startswith("admin:"))
    dp.message.register(set_new_source_bot, AdminStates.waiting_for_new_source)
    dp.message.register(process_broadcast, AdminStates.waiting_for_broadcast_msg)
    dp.message.register(process_balance_user_id, AdminStates.waiting_for_balance_user_id)
    dp.message.register(process_balance_amount, AdminStates.waiting_for_balance_amount)
    dp.message.register(process_setting_value, AdminStates.waiting_for_setting_value)
    dp.message.register(process_channel, AdminStates.waiting_for_channel)
    dp.message.register(process_log_channel, AdminStates.waiting_for_log_channel)
    dp.message.register(process_whitelist, AdminStates.waiting_for_whitelist)
    dp.message.register(process_blocklist, AdminStates.waiting_for_blocklist)
    dp.message.register(process_custom_price, AdminStates.waiting_for_custom_price)
