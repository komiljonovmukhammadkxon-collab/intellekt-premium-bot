import os
import sqlite3
import threading
import requests
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import LabeledPrice, PreCheckoutQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

# ==========================================
# 🔑 TOKENLAR
# ==========================================
BOT_TOKEN = "BU_YERGA_BOT_TOKENINGIZNI_YOZING"
CLICK_PROVIDER_TOKEN = "398062629:TEST:999999999_F91D8F69C042267444B74CC0B3C747757EB0E065"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

class SearchStates(StatesGroup):
    waiting_for_book = State()
    waiting_for_audio = State()

# 📊 Ma'lumotlar bazasi
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
        
    if downloads_today < 2:
        return True, "free"
    else:
        return False, "limit_out"

# ==========================================
# 🚀 BOT LOGIKASI
# ==========================================

@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    kb = [
        [types.KeyboardButton(text="📚 Kitob yuklash"), types.KeyboardButton(text="🎧 Audio eshitish")],
        [types.KeyboardButton(text="💎 Premium sotib olish")]
    ]
    keyboard = types.ReplyKeyboardMarkup(keyboard=keyboard=kb, resize_keyboard=True)
    await message.answer("🧠 INTELLEKT — 100% Avtomat kutubxona botiga xush kelibsiz!", reply_markup=keyboard)

@dp.message(F.text == "📚 Kitob yuklash")
async def ask_book(message: types.Message, state: FSMContext):
    allowed, status = check_limit(message.from_user.id)
    if allowed:
        await message.answer("🔍 Qidirayotgan kitobingiz nomini yozing:")
        await state.set_state(SearchStates.waiting_for_book)
    else:
        await message.answer("🚫 Bugungi bepul limitingiz tugadi! Davom etish uchun Premium sotib oling.")

# 🌐 INTERNETDAN AVTOMAT KITOB QIDIRISH
@dp.message(SearchStates.waiting_for_book)
async def fetch_book(message: types.Message, state: FSMContext):
    book_name = message.text
    status_msg = await message.answer("🔍 Internet kutubxonalaridan qidirilmoqda...")
    
    # Open Library Ochiq API orqali qidiruv
    url = f"https://openlibrary.org/search.json?q={book_name}"
    try:
        response = requests.get(url).json()
        if response.get("docs"):
            book_data = response["docs"][0]
            title = book_data.get("title", "Noma'lum")
            author = book_data.get("author_name", ["Noma'lum"])[0]
            
            # Yuklab olish havolasini shakllantirish
            download_url = f"https://openlibrary.org{book_data.get('key')}"
            
            # Limitni yangilash
            cursor.execute("SELECT is_premium FROM users WHERE user_id = ?", (message.from_user.id,))
            if cursor.fetchone()[0] == 0:
                cursor.execute("UPDATE users SET downloads_today = downloads_today + 1 WHERE user_id = ?", (message.from_user.id,))
                conn.commit()

            await status_msg.delete()
            
            inline_kb = [[types.InlineKeyboardButton(text="📥 PDF Yuklab olish", url=download_url)]]
            keyboard = types.InlineKeyboardMarkup(inline_keyboard=inline_kb)
            
            await message.answer(f"✅ Kitob topildi!\n\n📖 Nomi: {title}\n✍️ Muallif: {author}\n\nPastdagi tugma orqali PDF formatini yuklab oling:", reply_markup=keyboard)
        else:
            await status_msg.edit_text("❌ Afsuski, bu nomdagi kitob topilmadi. Boshqa nom yozib ko'ring.")
    except:
        await status_msg.edit_text("⚠️ Qidiruv tizimida xatolik yuz berdi. Birozdan so'ng urunib ko'ring.")
    
    await state.clear()

# 🎧 AVTOMAT AUDIO GENERATSIYA (TEXT-TO-SPEECH)
@dp.message(F.text == "🎧 Audio eshitish")
async def ask_audio(message: types.Message, state: FSMContext):
    allowed, status = check_limit(message.from_user.id)
    if allowed:
        await message.answer("🔍 Qaysi kitob yoki matnning audiosi kerak? Nomini yozing:")
        await state.set_state(SearchStates.waiting_for_audio)
    else:
        await message.answer("🚫 Bugungi bepul limitingiz tugadi! Premium sotib oling.")

@dp.message(SearchStates.waiting_for_audio)
async def generate_audio(message: types.Message, state: FSMContext):
    text_to_speak = message.text
    status_msg = await message.answer("🎙 Audio avtomat tayyorlanmoqda (Text-to-Speech)...")
    
    # Tekin Google TTS orqali matnni ovozga aylantirish linki
    tts_url = f"https://translate.google.com/translate_tts?ie=UTF-8&tl=uz&client=tw-ob&q={requests.utils.quote(text_to_speak)}"
    
    try:
        # Limitni yangilash
        cursor.execute("SELECT is_premium FROM users WHERE user_id = ?", (message.from_user.id,))
        if cursor.fetchone()[0] == 0:
            cursor.execute("UPDATE users SET downloads_today = downloads_today + 1 WHERE user_id = ?", (message.from_user.id,))
            conn.commit()
            
        await status_msg.delete()
        # Ovozli xabar sifatida linkni yuborish
        await bot.send_audio(chat_id=message.chat.id, audio=tts_url, title=f"{text_to_speak} (Audio-kitob)")
    except Exception as e:
        await status_msg.edit_text("❌ Kechirasiz, audioni tayyorlashda xatolik bo'ldi.")
        
    await state.clear()

# ==========================================
# 💳 CLICK TO'LOV (49 000 SO'M)
# ==========================================
@dp.message(F.text == "💎 Premium sotib olish")
async def buy_premium(message: types.Message):
    prices = [LabeledPrice(label="Premium Obuna (Umrbod)", amount=4900000)]
    await bot.send_invoice(
        chat_id=message.chat.id, title="INTELLEKT | PREMIUM",
        description="Barcha kitoblar va audiolarga umrbod cheksiz ruxsat.",
        provider_token=CLICK_PROVIDER_TOKEN, currency="UZS", prices=prices, payload="premium_upgrade"
    )

@dp.pre_checkout_query()
async def process_pre_checkout(pre_checkout_query: PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

@dp.message(F.successful_payment)
async def success_payment(message: types.Message):
    cursor.execute("UPDATE users SET is_premium = 1 WHERE user_id = ?", (message.from_user.id,))
    conn.commit()
    await message.answer("🎉 To'lov muvaffaqiyatli o'tdi! Endi siz Premiumsiz va cheklovlar yo'qoldi! 🚀")

# 🌐 SERVER
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200); self.end_headers(); self.wfile.write(b"Bot is alive")

def run_health_check():
    server = HTTPServer(('0.0.0.0', int(os.environ.get("PORT", 10000))), HealthCheckHandler)
    server.serve_forever()

if __name__ == "__main__":
    threading.Thread(target=run_health_check, daemon=True).start()
    dp.run_polling(bot)
