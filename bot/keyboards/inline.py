from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_admin_panel_keyboard() -> InlineKeyboardMarkup:
    # According to the image provided:
    # Danger = red, Success = green, Primary = blue

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        # Row 1
        [InlineKeyboardButton(text="Nomer berishni o'chirish", callback_data="admin:toggle_number_status")], # style equivalent: red/danger (not natively supported by aiogram out of the box in simple buttons without mini apps, but we use text for representation)

        # Row 2
        [
            InlineKeyboardButton(text="Whitelist", callback_data="admin:whitelist"),
            InlineKeyboardButton(text="Blocklist", callback_data="admin:blocklist")
        ],

        # Row 3
        [
            InlineKeyboardButton(text="Statistika", callback_data="admin:statistics"),
            InlineKeyboardButton(text="Resetall", callback_data="admin:resetall")
        ],

        # Row 4
        [InlineKeyboardButton(text="Broadcast", callback_data="admin:broadcast")],

        # Row 5
        [InlineKeyboardButton(text="Slot limit", callback_data="admin:slot_limit")],

        # Row 6
        [InlineKeyboardButton(text="Akkauntlar", callback_data="admin:accounts")],

        # Row 7
        [InlineKeyboardButton(text="Kanallar", callback_data="admin:channels")],

        # Row 8
        [InlineKeyboardButton(text="Beqaror raqamlar", callback_data="admin:unstable_numbers")],

        # Row 9
        [InlineKeyboardButton(text="Balansni o'zgartirish", callback_data="admin:change_balance")],

        # Row 10
        [InlineKeyboardButton(text="Narx o'zgartirish", callback_data="admin:change_price")],

        # Row 11
        [InlineKeyboardButton(text="Habarlarni o'chirish", callback_data="admin:delete_messages")],

        # Row 12
        [InlineKeyboardButton(text="Stat yuklab olish", callback_data="admin:download_stat")],

        # Row 13
        [InlineKeyboardButton(text="User narxi", callback_data="admin:user_price")]
    ])

    return keyboard

def get_accounts_keyboard(accounts) -> InlineKeyboardMarkup:
    buttons = []
    for acc in accounts:
        buttons.append([InlineKeyboardButton(text=f"{acc['phone_number']} ({acc['status']})", callback_data=f"admin:acc:{acc['id']}")])
    buttons.append([InlineKeyboardButton(text="➕ Akkaunt qo'shish", callback_data="admin:add_account")])
    buttons.append([InlineKeyboardButton(text="🔙 Orqaga", callback_data="admin:main")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)
