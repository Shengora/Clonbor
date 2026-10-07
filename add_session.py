import asyncio
import sys
from pyrogram import Client
from bot.database import db
from bot.database.db import init_db
from bot.core.config import API_ID, API_HASH

async def main():
    await init_db()
    if len(sys.argv) < 2:
        print("Usage: python3 add_session.py <phone_number>")
        return

    phone_number = sys.argv[1]

    print(f"Adding session for {phone_number}...")
    client = Client(name=f"temp_{phone_number}", api_id=API_ID, api_hash=API_HASH, in_memory=True)

    await client.connect()
    try:
        sent_code = await client.send_code(phone_number)
        code = input("Enter the code you received: ")
        await client.sign_in(phone_number, sent_code.phone_code_hash, code)

        session_string = await client.export_session_string()
        print("Session generated successfully!")

        await db.add_account(phone_number, session_string)
        print(f"Account {phone_number} saved to database.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
