import os
import sqlite3
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import LabeledPrice, PreCheckoutQuery

# 🔑 Tokenlarni bu yerga joylashtiring
BOT_TOKEN = "8931904012:AAF655P4Fk3eNbJ8ZMP_OOCtCybbCX8iHnc"
CLICK_PROVIDER_TOKEN = "398062629:TEST:999999999_F91D8F69C042267444B74CC0B3C747757EB0E065"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# 📊 Ma'lumotlar bazasini sozlash (SQLite)
conn = sqlite3.connect("users.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    is_premium INTEGER DEFAULT 0,
    downloads_today INTEGER DEFAULT 0,
    last_download_date TEXT
)
""")
conn.commit()

# 🔄 Limitlarni tekshirish
def check_limit(user_id):
    cursor.execute("SELECT is_premium, downloads_today, last_download_date FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    today = datetime.today().strftime('%Y-%m-%d')
    
    if not user:
        cursor.execute("INSERT INTO users (user_id, last_download_date) VALUES (?, ?)", (user_id, today))
        conn.commit()
        return True, "free"
    
    is_premium, downloads_today, last_download_date = user
    if is_premium == 1:
        return True, "premium"
        
    if last_download_date != today:
        cursor.execute("UPDATE users SET downloads_today = 0, last_download_date = ? WHERE user_id = ?", (today, user_id))
        conn.commit()
        downloads_today = 0
        
    if downloads_today < 2:  # 1 ta kitob + 1 ta audio
        return True, "free"
    else:
        return False, "limit_out"

# 🚀 /start
@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    kb = [
        [types.KeyboardButton(text="📚 Kitob yuklash"), types.KeyboardButton(text="🎧 Audio eshitish")],
        [types.KeyboardButton(text="💎 Premium sotib olish")]
    ]
    keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    await message.answer(
        "🧠 INTELLEKT botiga xush kelibsiz!\n\n"
        "Oddiy a'zolar kuniga 1 ta kitob va 1 ta audio yuklay olishadi. "
        "Premium a'zolarda esa mutlaqo cheksiz va avtomat tizim! 🚀", reply_markup=keyboard
    )

# 📚 Kitob yuklash bo'limi
@dp.message(F.text == "📚 Kitob yuklash")
async def get_book(message: types.Message):
    allowed, status = check_limit(message.from_user.id)
    if allowed:
        if status == "free":
            cursor.execute("UPDATE users SET downloads_today = downloads_today + 1 WHERE user_id = ?", (message.from_user.id,))
            conn.commit()
        await message.answer("📖 Mana siz so'ragan kitob PDF formati! (Avtomat yuklandi)")
    else:
        await message.answer(
            "🚫 Bugungi bepul limitingiz tugadi!\n\n"
            "Kutib o'tirmasdan barcha kitoblarni hoziroq cheksiz yuklab olish uchun pastdagi "
            "\"💎 Premium sotib olish\" tugmasini bosing."
        )

# 💎 Click orqali faktura (Invoice) chiqarish
@dp.message(F.text == "💎 Premium sotib olish")
async def buy_premium(message: types.Message):
    # Click tizimida summa to'g'ridan-to'g'ri so'mda ko'rsatiladi (Masalan: 49000 so'm)
    prices = [LabeledPrice(label="Premium Obuna (Umrbod)", amount=49000)]
    
    await bot.send_invoice(
        chat_id=message.chat.id,
        title="INTELLEKT | PREMIUM STATUS",
        description="Botdagi barcha kitoblar va audiolarga umrbod cheksiz ruxsat olish.",
        provider_token=CLICK_PROVIDER_TOKEN,
        currency="UZS",
        prices=prices,
        payload="premium_upgrade_via_click"
    )

# 💰 To'lovdan oldingi so'rovni avtomat tasdiqlash
@dp.pre_checkout_query()
async def process_pre_checkout(pre_checkout_query: PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

# ✅ Click orqali pul tushishi bilan 100% AVTOMAT ishlaydigan qism
@dp.message(F.successful_payment)
async def success_payment_handler(message: types.Message):
    user_id = message.from_user.id
    
    # Bazada foydalanuvchini Premium qilish
    cursor.execute("UPDATE users SET is_premium = 1 WHERE user_id = ?", (user_id,))
    conn.commit()
    
    await message.answer(
        "🎉 Tabriklaymiz! Click orqali to'lovingiz muvaffaqiyatli qabul qilindi.\n"
        "Sizga PREMIUM statusi berildi. Endi barcha cheklovlar olib tashlandi! 🚀"
    )

if __name__ == "__main__":
    dp.run_polling(bot)
