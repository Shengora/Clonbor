from bot.handlers.user import register_user_handlers
from bot.handlers.admin import register_admin_handlers
from bot.handlers.session_creator import register_session_handlers

def register_all_handlers(dp):
    register_user_handlers(dp)
    register_admin_handlers(dp)
    register_session_handlers(dp)
