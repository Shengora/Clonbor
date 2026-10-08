from aiogram.fsm.state import State, StatesGroup

class AdminStates(StatesGroup):
    waiting_for_new_source = State()
    waiting_for_phone = State()
    waiting_for_code = State()
    waiting_for_password = State()

    # New Admin States
    waiting_for_broadcast_msg = State()
    waiting_for_balance_user_id = State()
    waiting_for_balance_amount = State()
    waiting_for_setting_value = State()
    waiting_for_channel = State()
    waiting_for_whitelist = State()
    waiting_for_blocklist = State()

class UserStates(StatesGroup):
    waiting_for_wallet = State()
    waiting_for_withdraw_amount = State()
