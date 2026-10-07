import aiosqlite
import logging

from bot.core.config import DB_PATH

logger = logging.getLogger(__name__)

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE,
                balance INTEGER DEFAULT 0,
                premium_count INTEGER DEFAULT 0,
                canceled_numbers INTEGER DEFAULT 0,
                frozen_numbers INTEGER DEFAULT 0,
                codes_received INTEGER DEFAULT 0,
                joined_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                state TEXT DEFAULT 'active'
            )
        ''')

        await db.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        ''')

        await db.execute('''
            CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                phone_number TEXT UNIQUE,
                session_string TEXT,
                status TEXT DEFAULT 'active'
            )
        ''')

        await db.execute('''
            CREATE TABLE IF NOT EXISTS statistics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE DEFAULT CURRENT_DATE UNIQUE,
                premium_count INTEGER DEFAULT 0,
                total_spent INTEGER DEFAULT 0
            )
        ''')

        from bot.core.config import SOURCE_BOT_USERNAME

        # Insert default settings if not exists
        default_settings = [
            ('slot_limit', '20'),
            ('number_status', '1'),  # 1 for active, 0 for inactive
            ('user_price', '5000'), # default price added to user balance
            ('source_bot', SOURCE_BOT_USERNAME) # active source bot username
        ]

        for key, value in default_settings:
            await db.execute('INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)', (key, value))

        await db.commit()
        logger.info("Database initialized successfully.")

# --- Users ---
async def get_user(telegram_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute('SELECT * FROM users WHERE telegram_id = ?', (telegram_id,)) as cursor:
            return await cursor.fetchone()

async def add_user(telegram_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('INSERT OR IGNORE INTO users (telegram_id) VALUES (?)', (telegram_id,))
        await db.commit()

async def update_user_balance(telegram_id: int, amount: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('UPDATE users SET balance = balance + ? WHERE telegram_id = ?', (amount, telegram_id))
        await db.commit()

async def increment_user_premium_count(telegram_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('UPDATE users SET premium_count = premium_count + 1 WHERE telegram_id = ?', (telegram_id,))
        await db.commit()

async def increment_user_codes_received(telegram_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('UPDATE users SET codes_received = codes_received + 1 WHERE telegram_id = ?', (telegram_id,))
        await db.commit()

async def increment_user_canceled_numbers(telegram_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('UPDATE users SET canceled_numbers = canceled_numbers + 1 WHERE telegram_id = ?', (telegram_id,))
        await db.commit()

async def increment_user_frozen_numbers(telegram_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('UPDATE users SET frozen_numbers = frozen_numbers + 1 WHERE telegram_id = ?', (telegram_id,))
        await db.commit()

async def get_total_users_count():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute('SELECT COUNT(*) FROM users') as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 0

async def get_total_balance():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute('SELECT SUM(balance) FROM users') as cursor:
            row = await cursor.fetchone()
            return row[0] if row and row[0] else 0

# --- Settings ---
async def get_setting(key: str):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute('SELECT value FROM settings WHERE key = ?', (key,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else None

async def set_setting(key: str, value: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)', (key, value))
        await db.commit()

# --- Accounts ---
async def get_all_accounts():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute('SELECT * FROM accounts') as cursor:
            return await cursor.fetchall()

async def get_active_account():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute('SELECT * FROM accounts WHERE status = "active" LIMIT 1') as cursor:
            return await cursor.fetchone()

async def add_account(phone_number: str, session_string: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('INSERT OR IGNORE INTO accounts (phone_number, session_string) VALUES (?, ?)', (phone_number, session_string))
        await db.commit()

async def delete_account(account_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('DELETE FROM accounts WHERE id = ?', (account_id,))
        await db.commit()

# --- Statistics ---
async def update_statistics(spent_amount: int):
    async with aiosqlite.connect(DB_PATH) as db:
        # First, try to insert for today if it doesn't exist
        await db.execute('''
            INSERT OR IGNORE INTO statistics (date, premium_count, total_spent)
            VALUES (CURRENT_DATE, 0, 0)
        ''')
        # Then update
        await db.execute('''
            UPDATE statistics
            SET premium_count = premium_count + 1, total_spent = total_spent + ?
            WHERE date = CURRENT_DATE
        ''', (spent_amount,))
        await db.commit()

async def get_today_statistics():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute('SELECT * FROM statistics WHERE date = CURRENT_DATE') as cursor:
            return await cursor.fetchone()

async def get_total_premium_count():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute('SELECT SUM(premium_count) FROM statistics') as cursor:
            row = await cursor.fetchone()
            return row[0] if row and row[0] else 0
