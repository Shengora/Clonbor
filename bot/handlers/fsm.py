from aiogram.fsm.state import State, StatesGroup

class AdminStates(StatesGroup):
    waiting_for_new_source = State()
    waiting_for_phone = State()
    waiting_for_code = State()
    waiting_for_password = State()
