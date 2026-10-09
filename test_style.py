from aiogram.types import InlineKeyboardButton
try:
    btn = InlineKeyboardButton(text="Test", callback_data="test", style="danger")
    print("Success! style works.")
except Exception as e:
    print("Error:", type(e), e)
