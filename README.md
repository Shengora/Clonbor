# Telegram Middleman Bot

Bu bot foydalanuvchilar va boshqa bir (manba) Telegram bot o'rtasida vositachi (middleman) vazifasini bajaradi. Foydalanuvchilar raqam so'raganda, bot orqadagi (Userbot) akkauntlar orqali manba botidan raqam olib beradi va agar foydalanuvchi muvaffaqiyatli premium olsa, ularning balansiga pul qo'shadi.

## O'rnatish

1. Talablarni o'rnatish:
   ```bash
   pip install -r requirements.txt
   ```

2. `.env` faylini yaratish:
   ```bash
   cp .env.example .env
   ```
   Va ichidagi ma'lumotlarni o'zingiznikiga o'zgartiring (BOT_TOKEN, ADMIN_IDS, API_ID, API_HASH, SOURCE_BOT_USERNAME).

3. Botni ishga tushirish:
   ```bash
   export PYTHONPATH=$(pwd)
   python3 bot/main.py
   ```

4. Manba bot bilan ishlovchi akkauntlarni (Userbot) qo'shish:
   Botni ishga tushirgach, `/admin` buyrug'i orqali Admin panelga kiring. U yerdagi "Akkauntlar" va "➕ Akkaunt qo'shish" tugmasi orqali to'g'ridan-to'g'ri bot ichida telefon raqam, kod va (agar mavjud bo'lsa) 2FA parolini kiritib, yangi manba akkauntlarini ulashingiz mumkin.

## Xususiyatlar
- Foydalanuvchilar balansini boshqarish
- Manba botidan tugmalar bilan ishlash va ularni userlarga forward qilish
- Pyrogram + Aiogram3 asosida to'liq asinxron arxitektura
- Admin panel orqali statistika va akkauntlarni boshqarish
