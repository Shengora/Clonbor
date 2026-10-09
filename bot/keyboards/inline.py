from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_admin_panel_keyboard() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        # Row 1
        [InlineKeyboardButton(text="🔴 Nomer berishni o'chirish", callback_data="admin:toggle_number_status")],

        # Row 2
        [
            InlineKeyboardButton(text="🟢 Whitelist", callback_data="admin:whitelist"),
            InlineKeyboardButton(text="🟢 Blocklist", callback_data="admin:blocklist")
        ],

        # Row 3
        [
            InlineKeyboardButton(text="🔵 Statistika", callback_data="admin:statistics"),
            InlineKeyboardButton(text="🔵 Resetall", callback_data="admin:resetall")
        ],

        # Row 4
        [InlineKeyboardButton(text="🔵 Broadcast", callback_data="admin:broadcast")],

        # Row 5
        [InlineKeyboardButton(text="🔵 Slot limit", callback_data="admin:slot_limit")],

        # Row 6
        [InlineKeyboardButton(text="🔵 Akkauntlar", callback_data="admin:accounts")],

        # Row 7
        [InlineKeyboardButton(text="🔵 Kanallar", callback_data="admin:channels")],

        # Row 8
        [InlineKeyboardButton(text="🔵 Beqaror raqamlar", callback_data="admin:unstable_numbers")],

        # Row 9
        [InlineKeyboardButton(text="🔵 Balansni o'zgartirish", callback_data="admin:change_balance")],

        # Row 10
        [InlineKeyboardButton(text="🔵 Habarlarni o'chirish", callback_data="admin:delete_messages")],

        # Row 12
        [InlineKeyboardButton(text="🔵 Stat yuklab olish", callback_data="admin:download_stat")],

        # Row 13
        [InlineKeyboardButton(text="🔵 User narxi", callback_data="admin:user_price")],

        # Row 14
        [InlineKeyboardButton(text="🔵 Log Kanal", callback_data="admin:log_channel")],

        # Row 15
        [InlineKeyboardButton(text="🔵 Manbalar", callback_data="admin:sources")]
    ])

    return keyboard

def get_sources_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Joriy manba haqida", callback_data="admin:source_info")],
        [InlineKeyboardButton(text="Manba botni o'zgartirish", callback_data="admin:source_change")],
        [InlineKeyboardButton(text="🔙 Orqaga", callback_data="admin:main")]
    ])

def get_back_to_main_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Orqaga", callback_data="admin:main")]
    ])

def get_accounts_keyboard(accounts) -> InlineKeyboardMarkup:
    buttons = []
    for acc in accounts:
        buttons.append([InlineKeyboardButton(text=f"{acc['phone_number']} ({acc['status']})", callback_data=f"admin:acc:{acc['id']}")])
    buttons.append([InlineKeyboardButton(text="➕ Akkaunt qo'shish", callback_data="admin:add_account")])
    buttons.append([InlineKeyboardButton(text="🔙 Orqaga", callback_data="admin:main")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_users_price_keyboard(users, current_page: int, total_pages: int) -> InlineKeyboardMarkup:
    buttons = []

    # Global price button at the top
    buttons.append([InlineKeyboardButton(text="🌍 Barchaga umumiy narxni o'rnatish", callback_data="admin:global_price_set")])

    # User buttons
    for u in users:
        uname = f"@{u['username']}" if u['username'] else f"{u['first_name']}"
        try:
            custom_price = u['custom_price']
        except Exception:
            custom_price = None
        price_text = f"{custom_price} so'm" if custom_price is not None else "Umumiy narx"
        btn_text = f"👤 {uname} - {price_text}"
        buttons.append([InlineKeyboardButton(text=btn_text, callback_data=f"admin:set_user_price:{u['telegram_id']}")])

    # Pagination
    nav_buttons = []
    if current_page > 0:
        nav_buttons.append(InlineKeyboardButton(text="⬅️ Oldingi", callback_data=f"admin:user_price_page:{current_page-1}"))
    if current_page < total_pages - 1:
        nav_buttons.append(InlineKeyboardButton(text="Keyingi ➡️", callback_data=f"admin:user_price_page:{current_page+1}"))

    if nav_buttons:
        buttons.append(nav_buttons)

    buttons.append([InlineKeyboardButton(text="🔙 Orqaga", callback_data="admin:main")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)
