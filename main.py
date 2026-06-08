import os
import sqlite3
import threading
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import LabeledPrice, PreCheckoutQuery

# ==========================================
# 🔑 TOKENLARNI SHU YERGA JOYLASHTIRING
# ==========================================
BOT_TOKEN = "8931904012:AAF655P4Fk3eNbJ8ZMP_OOCtCybbCX8iHnc"
CLICK_PROVIDER_TOKEN = "398062629:TEST:999999999_F91D8F69C042267444B74CC0B3C747757EB0E065"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ==========================================
# 📊 MA'LUMOTLAR BAZASI (SQLite)
# ==========================================
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

# ==========================================
# 🔄 LIMITLARNI TEKSHIRISH FUNKSIYASI
# ==========================================
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
        
    if downloads_today < 2:  # 1 ta kitob + 1 ta audio = jami 2 ta yuklash
        return True, "free"
    else:
        return False, "limit_out"

# ==========================================
# 🚀 BOT BUYRUQLARI VA LOGIKASI
# ==========================================

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

@dp.message(F.text == "🎧 Audio eshitish")
async def get_audio(message: types.Message):
    allowed, status = check_limit(message.from_user.id)
    if allowed:
        if status == "free":
            cursor.execute("UPDATE users SET downloads_today = downloads_today + 1 WHERE user_id = ?", (message.from_user.id,))
            conn.commit()
        await message.answer("🎧 Mana siz so'ragan audio-konspekt! (Avtomat yuklandi)")
    else:
        await message.answer(
            "🚫 Bugungi bepul limitingiz tugadi!\n\n"
            "Kutib o'tirmasdan barcha audiolarni hoziroq cheksiz eshitish uchun pastdagi "
            "\"💎 Premium sotib olish\" tugmasini bosing."
        )

# ==========================================
# 💳 CLICK AVTOMAT TO'LOV TIZIMI
# ==========================================

@dp.message(F.text == "💎 Premium sotib olish")
async def buy_premium(message: types.Message):
    prices = [LabeledPrice(label="Premium Obuna (Umrbod)", amount=49000)] # Click so'mda qabul qiladi
    
    await bot.send_invoice(
        chat_id=message.chat.id,
        title="INTELLEKT | PREMIUM STATUS",
        description="Botdagi barcha kitoblar va audiolarga umrbod cheksiz ruxsat olish.",
        provider_token=CLICK_PROVIDER_TOKEN,
        currency="UZS",
        prices=prices,
        payload="premium_upgrade_via_click"
    )

@dp.pre_checkout_query()
async def process_pre_checkout(pre_checkout_query: PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

@dp.message(F.successful_payment)
async def success_payment_handler(message: types.Message):
    user_id = message.from_user.id
    cursor.execute("UPDATE users SET is_premium = 1 WHERE user_id = ?", (user_id,))
    conn.commit()
    
    await message.answer(
        "🎉 Tabriklaymiz! Click orqali to'lovingiz muvaffaqiyatli qabul qilindi.\n"
        "Sizga PREMIUM statusi berildi. Endi barcha cheklovlar olib tashlandi! 🚀"
    )

# ==========================================
# 🌐 SERVER PORTINI ESHITISH (TEKIN SERVERLAR UCHUN)
# ==========================================
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is alive")

def run_health_check():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    server.serve_forever()

if __name__ == "__main__":
    # Tekin serverlar o'chib qolmasligi uchun feyk-serverni fonda yoqamiz
    threading.Thread(target=run_health_check, daemon=True).start()
    
    # Botni ishga tushiramiz
    dp.run_polling(bot)
