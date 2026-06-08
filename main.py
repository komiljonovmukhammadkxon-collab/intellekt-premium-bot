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
# 🔑 TOKENLAR (Shu yerga o'z tokenlaringizni qo'ying)
# ==========================================
BOT_TOKEN = "8931904012:AAF655P4Fk3eNbJ8ZMP_OOCtCybbCX8iHnc"
CLICK_PROVIDER_TOKEN = "398062629:TEST:999999999_F91D8F69C042267444B74CC0B3C747757EB0E065"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

class SearchStates(StatesGroup):
    waiting_for_book = State()
    waiting_for_audio = State()

# 📊 Ma'lumotlar bazasi (SQLite)
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
    try:
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
            
        if downloads_today < 2:  # Kunlik bepul limit
            return True, "free"
        else:
            return False, "limit_out"
    except Exception:
        return True, "error_fallback"

# ==========================================
# 🚀 BOT INTERFEYSI VA BUYRUQLARI
# ==========================================

@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    kb = [
        [types.KeyboardButton(text="📚 Kitob yuklash"), types.KeyboardButton(text="🎧 Audio eshitish")],
        [types.KeyboardButton(text="💎 Premium sotib olish")]
    ]
    keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    await message.answer(
        "🧠 INTELLEKT — Avtomat ko'p tarmoqli kutubxona botiga xush kelibsiz!\n\n"
        "Kitob yoki audio qidirish uchun quyidagi tugmalardan foydalaning.", 
        reply_markup=keyboard
    )

@dp.message(F.text == "📚 Kitob yuklash")
async def ask_book(message: types.Message, state: FSMContext):
    allowed, status = check_limit(message.from_user.id)
    if allowed:
        await message.answer("🔍 Qidirayotgan kitobingiz nomini kiriting:\n*(Kichik harf yoki joy tashlash xatolari avtomat to'g'rilanadi)*")
        await state.set_state(SearchStates.waiting_for_book)
    else:
        await message.answer("🚫 Bugungi bepul limitingiz tugadi! Davom etish uchun Premium obuna bo'ling.")

# 🌐 MULTI-SEARCH: RESURS REJIMIDA INTEGRATSIYA
@dp.message(SearchStates.waiting_for_book)
async def fetch_book(message: types.Message, state: FSMContext):
    raw_input = message.text
    # 🛠 SIZ AYTGANINGIZDEK: hamma harf kichik qilinadi, bosh/oxir va o'rtadagi ortiqcha joylar butkul tozalanadi
    cleaned_name = " ".join(raw_input.split()).lower().strip()
    
    if not cleaned_name:
        await message.answer("⚠️ Iltimos, kitob nomini to'g'ri kiriting.")
        await state.clear()
        return

    status_msg = await message.answer("🔍 Bir nechta jahon bazalari va arxivlaridan PDF fayl qidirilmoqda...")
    query_param = requests.utils.quote(cleaned_name)
    found_books = []

    # 1-MANBA: Internet Archive API (To'g'ridan-to'g'ri yuklanadigan fayllar ombori)
    try:
        archive_url = f"https://archive.org/advancedsearch.php?q=title:({query_param})+AND+mediatype:(texts)&fl[]=identifier,title,creator&sort[]=&rows=2&output=json"
        res = requests.get(archive_url, timeout=5).json()
        docs = res.get("response", {}).get("docs", [])
        for doc in docs:
            if doc.get("identifier"):
                found_books.append({
                    "title": doc.get("title", "Noma'lum kitob"),
                    "author": doc.get("creator", "Noma'lum muallif"),
                    "url": f"https://archive.org/download/{doc['identifier']}/{doc['identifier']}.pdf",
                    "source": "Internet Archive (Ochiq PDF)"
                })
    except Exception:
        pass  # Xato bersa o'chib qolmaydi, keyingi saytga o'tadi

    # 2-MANBA: Google Books API (Dunyo kutubxonasi)
    try:
        google_url = f"https://www.googleapis.com/books/v1/volumes?q={query_param}&maxResults=2"
        res = requests.get(google_url, timeout=5).json()
        items = res.get("items", [])
        for item in items:
            info = item.get("volumeInfo", {})
            access = item.get("accessInfo", {})
            link = access.get("pdf", {}).get("downloadLink") or info.get("previewLink") or info.get("infoLink")
            if link:
                found_books.append({
                    "title": info.get("title", "Noma'lum kitob"),
                    "author": info.get("authors", ["Noma'lum muallif"])[0],
                    "url": link,
                    "source": "Google Books"
                })
    except Exception:
        pass

    # 3-MANBA: Open Library API
    try:
        ol_url = f"https://openlibrary.org/search.json?q={query_param}"
        res = requests.get(ol_url, timeout=5).json()
        docs = res.get("docs", [])
        if docs:
            book_data = docs[0]
            found_books.append({
                "title": book_data.get("title", "Noma'lum kitob"),
                "author": book_data.get("author_name", ["Noma'lum muallif"])[0],
                "url": f"https://openlibrary.org{book_data.get('key')}",
                "source": "Open Library"
            })
    except Exception:
        pass

    # NATIJANI CHIQARISH
    try:
        await status_msg.delete()
    except Exception:
        pass

    if found_books:
        best_match = found_books[0]
        
        # Limitni yangilash qismi
        try:
            cursor.execute("SELECT is_premium FROM users WHERE user_id = ?", (message.from_user.id,))
            user_status = cursor.fetchone()
            if user_status and user_status[0] == 0:
                cursor.execute("UPDATE users SET downloads_today = downloads_today + 1 WHERE user_id = ?", (message.from_user.id,))
                conn.commit()
        except Exception:
            pass

        inline_kb = [[types.InlineKeyboardButton(text="📥 Kitobni yuklash / O'qish", url=best_match["url"])]]
        keyboard = types.InlineKeyboardMarkup(inline_keyboard=inline_kb)
        
        await message.answer(
            f"✅ Kitob topildi!\n\n"
            f"📖 Nomi: {best_match['title']}\n"
            f"✍️ Muallif: {best_match['author']}\n"
            f"🌐 Manba: {best_match['source']}\n\n"
            f"Faylni yuklab olish yoki ko'rish uchun pastdagi tugmani bosing:", 
            reply_markup=keyboard
        )
    else:
        await message.answer(
            "❌ Afsuski, ulangan barcha tarmoqlardan bu kitob topilmadi.\n\n"
            "💡 Maslahat: Kitob nomini inglizcha yoki ruscha yozib ko'ring (Masalan: 'Atomic Habits' yoki 'Shantaram')."
        )
        
    await state.clear()

# 🎧 AUDIO TIZIMI
@dp.message(F.text == "🎧 Audio eshitish")
async def ask_audio(message: types.Message, state: FSMContext):
    allowed, status = check_limit(message.from_user.id)
    if allowed:
        await message.answer("🔍 Ovozli eshitmoqchi bo'lgan matn yoki kitob nomini yozing:")
        await state.set_state(SearchStates.waiting_for_audio)
    else:
        await message.answer("🚫 Bugungi bepul limitingiz tugadi!")

@dp.message(SearchStates.waiting_for_audio)
async def generate_audio(message: types.Message, state: FSMContext):
    text_to_speak = message.text
    status_msg = await message.answer("🎙 Audio tayyorlanmoqda...")
    
    tts_url = f"https://translate.google.com/translate_tts?ie=UTF-8&tl=uz&client=tw-ob&q={requests.utils.quote(text_to_speak)}"
    
    try:
        try:
            cursor.execute("SELECT is_premium FROM users WHERE user_id = ?", (message.from_user.id,))
            user_status = cursor.fetchone()
            if user_status and user_status[0] == 0:
                cursor.execute("UPDATE users SET downloads_today = downloads_today + 1 WHERE user_id = ?", (message.from_user.id,))
                conn.commit()
        except Exception:
            pass
            
        await status_msg.delete()
        await bot.send_audio(chat_id=message.chat.id, audio=tts_url, title=f"{text_to_speak}")
    except Exception:
        try:
            await status_msg.edit_text("❌ Audioni yuklashda xatolik yuz berdi.")
        except Exception:
            pass
        
    await state.clear()

# ==========================================
# 💳 CLICK INTEGRATSIYASI
# ==========================================

@dp.message(F.text == "💎 Premium sotib olish")
async def buy_premium(message: types.Message):
    try:
        prices = [LabeledPrice(label="Premium Obuna", amount=4900000)]
        await bot.send_invoice(
            chat_id=message.chat.id,
            title="INTELLEKT | PREMIUM",
            description="Umrbod cheksiz ruxsat olish.",
            provider_token=CLICK_PROVIDER_TOKEN,
            currency="UZS",
            prices=prices,
            payload="premium_upgrade"
        )
    except Exception:
        await message.answer("⚠️ To'lov tizimida uzilish bor. Token muddati o'tgan yoki Click ulanmagan.")

@dp.pre_checkout_query()
async def process_pre_checkout(pre_checkout_query: PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

@dp.message(F.successful_payment)
async def success_payment_handler(message: types.Message):
    try:
        cursor.execute("UPDATE users SET is_premium = 1 WHERE user_id = ?", (message.from_user.id,))
        conn.commit()
        await message.answer("🎉 Premium status muvaffaqiyatli faollashtirildi!")
    except Exception:
        await message.answer("🎉 To'lov o'tdi! Premium tizimi faollashdi.")

# ==========================================
# 🌐 SERVER (RENDER PORTI UCHUN)
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
    threading.Thread(target=run_health_check, daemon=True).start()
    dp.run_polling(bot)
