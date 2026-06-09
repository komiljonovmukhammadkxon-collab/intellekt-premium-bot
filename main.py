# ╔══════════════════════════════════════════════════════════════╗
# ║           🧠 INTELLEKT BOT — To'liq versiya                 ║
# ║           Muallif: Siz | Texnik: Claude                     ║
# ║           Til: O'zbek + Rus | To'lov: Telegram Stars        ║
# ╚══════════════════════════════════════════════════════════════╝

import os
import asyncio
import sqlite3
import threading
import requests
import tempfile
from datetime import datetime, timedelta
from http.server import BaseHTTPRequestHandler, HTTPServer

import edge_tts
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import LabeledPrice, PreCheckoutQuery, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🔑 1. TOKENLAR — Render.com da Environment Variables ga yozing
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
BOT_TOKEN = os.environ.get("BOT_TOKEN", "TOKENINGIZNI_BU_YERGA_YOZING")
ADMIN_ID  = int(os.environ.get("ADMIN_ID", "0"))

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 💬 2. XABARLAR MATNI (O'zbek + Rus)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MSG = {
    "start": (
        "👋 *INTELLEKT* ga xush kelibsiz!\n"
        "👋 *Добро пожаловать в INTELLEKT!*\n\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "📚 Kitob qidiring → PDF yuboriladi\n"
        "📚 Найдите книгу → получите PDF\n\n"
        "🎧 Matnni ovozga aylantiring\n"
        "🎧 Преобразуйте текст в аудио\n\n"
        "💎 Premium → cheksiz foydalaning\n"
        "💎 Premium → безлимитный доступ\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "🆓 Bepul: kuniga *2 ta* so'rov\n"
        "🆓 Бесплатно: *2 запроса* в день"
    ),
    "ask_book": (
        "🔍 *Kitob nomini kiriting:*\n"
        "🔍 *Введите название книги:*\n\n"
        "💡 Inglizcha yozsangiz natija ko'proq\n"
        "💡 На английском результатов больше"
    ),
    "searching": "⏳ Qidirilmoqda... | Идёт поиск...",
    "sending_pdf": "📤 PDF yuklanmoqda... | Загрузка PDF...",
    "book_not_found": (
        "❌ *Kitob topilmadi*\n"
        "❌ *Книга не найдена*\n\n"
        "💡 Maslahat | Совет:\n"
        "• Inglizcha yozing | Пишите по-английски\n"
        "• Muallif nomini qo'shing | Добавьте автора\n"
        "• Misol: `Atomic Habits James Clear`"
    ),
    "ask_audio": (
        "🎙 *Ovozga aylantirmoqchi bo'lgan matningizni yozing:*\n"
        "🎙 *Введите текст для озвучивания:*\n\n"
        "📝 Maksimal 3000 belgi | Максимум 3000 символов\n"
        "🌍 O'zbek, Rus, Ingliz tillarida ishlaydi"
    ),
    "audio_making": "🎙 Audio tayyorlanmoqda... | Создание аудио...",
    "audio_error": (
        "❌ Audio yaratishda xatolik!\n"
        "❌ Ошибка при создании аудио!\n"
        "🔄 Qayta urinib ko'ring | Попробуйте снова"
    ),
    "text_too_long": (
        "⚠️ Matn juda uzun! Maksimal 3000 belgi.\n"
        "⚠️ Текст слишком длинный! Максимум 3000 символов."
    ),
    "limit_out": (
        "🚫 *Bugungi 2 ta bepul limitingiz tugadi!*\n"
        "🚫 *Ваш бесплатный лимит (2 запроса) исчерпан!*\n\n"
        "💎 Premium olib cheksiz foydalaning\n"
        "💎 Купите Premium для безлимитного доступа"
    ),
    "premium_menu": (
        "💎 *INTELLEKT PREMIUM*\n\n"
        "✅ Cheksiz kitob yuklash | Безлимитные книги\n"
        "✅ Cheksiz audio | Безлимитное аудио\n"
        "✅ Tezkor qidiruv | Быстрый поиск\n\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "⭐ *Telegram Stars* bilan to'lang:\n"
        "⭐ Оплата через *Telegram Stars:*"
    ),
    "premium_success": (
        "🎉 *Premium muvaffaqiyatli faollashdi!*\n"
        "🎉 *Premium успешно активирован!*\n\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "✅ Cheksiz kitob va audio xizmatidan foydalaning\n"
        "✅ Пользуйтесь безлимитными книгами и аудио\n\n"
        "🙏 Xarid uchun rahmat! | Спасибо за покупку!"
    ),
    "big_file": (
        "📎 PDF fayl juda katta yoki himoyalangan.\n"
        "📎 PDF слишком большой или защищён.\n"
        "👇 Quyidagi havoladan oching | Откройте по ссылке:"
    ),
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🤖 3. BOT VA DISPATCHER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
bot = Bot(token=BOT_TOKEN)
dp  = Dispatcher()

class States(StatesGroup):
    waiting_for_book  = State()
    waiting_for_audio = State()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🗄 4. MA'LUMOTLAR BAZASI (SQLite)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
conn   = sqlite3.connect("users.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id           INTEGER PRIMARY KEY,
        username          TEXT,
        full_name         TEXT,
        premium_type      TEXT    DEFAULT NULL,
        premium_until     TEXT    DEFAULT NULL,
        downloads_today   INTEGER DEFAULT 0,
        last_download_date TEXT,
        joined_date       TEXT
    )
""")
conn.commit()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🔧 5. YORDAMCHI FUNKSIYALAR
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def register_user(user_id: int, username: str, full_name: str):
    """Yangi foydalanuvchini bazaga qo'shish (agar yo'q bo'lsa)"""
    today = datetime.today().strftime('%Y-%m-%d')
    cursor.execute("""
        INSERT OR IGNORE INTO users
        (user_id, username, full_name, last_download_date, joined_date)
        VALUES (?, ?, ?, ?, ?)
    """, (user_id, username, full_name, today, today))
    conn.commit()

def get_user(user_id: int):
    """Foydalanuvchi ma'lumotlarini olish"""
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    return cursor.fetchone()

def is_premium(user_id: int) -> bool:
    """Foydalanuvchi premium ekanligini tekshirish"""
    user = get_user(user_id)
    if not user:
        return False
    ptype, puntil = user[3], user[4]
    if ptype == "lifetime":
        return True
    if puntil:
        return datetime.today() <= datetime.strptime(puntil, '%Y-%m-%d')
    return False

def set_premium(user_id: int, plan: str):
    """Foydalanuvchiga premium berish"""
    today = datetime.today()
    durations = {"1day": 1, "1month": 30, "3month": 90}
    if plan == "lifetime":
        until = None
    else:
        until = (today + timedelta(days=durations.get(plan, 30))).strftime('%Y-%m-%d')
    cursor.execute(
        "UPDATE users SET premium_type = ?, premium_until = ? WHERE user_id = ?",
        (plan, until, user_id)
    )
    conn.commit()

def check_limit(user_id: int):
    """Kunlik limitni tekshirish"""
    if is_premium(user_id):
        return True, "premium"
    user = get_user(user_id)
    if not user:
        return True, "free"
    today = datetime.today().strftime('%Y-%m-%d')
    downloads, last_date = user[5], user[6]
    if last_date != today:
        cursor.execute(
            "UPDATE users SET downloads_today = 0, last_download_date = ? WHERE user_id = ?",
            (today, user_id)
        )
        conn.commit()
        downloads = 0
    return (True, "free") if downloads < 2 else (False, "limit_out")

def increment_download(user_id: int):
    """Kunlik yuklash hisoblagichini oshirish"""
    if not is_premium(user_id):
        cursor.execute(
            "UPDATE users SET downloads_today = downloads_today + 1 WHERE user_id = ?",
            (user_id,)
        )
        conn.commit()

def get_status_text(user_id: int) -> str:
    """Foydalanuvchi status matnini olish"""
    user = get_user(user_id)
    if not user:
        return "🆓 Bepul | Бесплатно"
    ptype, puntil = user[3], user[4]
    if ptype == "lifetime":
        return "💎 Umrbod Premium | Пожизненный Premium"
    if puntil and datetime.today() <= datetime.strptime(puntil, '%Y-%m-%d'):
        days_left = (datetime.strptime(puntil, '%Y-%m-%d') - datetime.today()).days
        labels = {"1day": "Kunlik|Дневной", "1month": "Oylik|Месячный", "3month": "3 Oylik|3 Месяца"}
        label = labels.get(ptype, "Premium")
        return f"✅ {label} — {days_left} kun | дней qoldi"
    return "🆓 Bepul | Бесплатно (kuniga 2 ta | 2 в день)"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🎹 6. ASOSIY KLAVIATURA
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def main_keyboard():
    return types.ReplyKeyboardMarkup(
        keyboard=[
            [
                types.KeyboardButton(text="📚 Kitob | Книга"),
                types.KeyboardButton(text="🎧 Audio")
            ],
            [
                types.KeyboardButton(text="💎 Premium"),
                types.KeyboardButton(text="👤 Profil | Профиль")
            ],
        ],
        resize_keyboard=True
    )

def limit_keyboard():
    return types.InlineKeyboardMarkup(inline_keyboard=[[
        types.InlineKeyboardButton(text="💎 Premium olish | Купить Premium", callback_data="show_premium")
    ]])

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🚀 7. /START BUYRUG'I
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user = message.from_user
    register_user(user.id, user.username or "", user.full_name or "")
    await message.answer(MSG["start"], reply_markup=main_keyboard(), parse_mode="Markdown")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 👤 8. PROFIL
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@dp.message(F.text == "👤 Profil | Профиль")
async def cmd_profile(message: types.Message):
    user = message.from_user
    register_user(user.id, user.username or "", user.full_name or "")
    db_user = get_user(user.id)
    downloads  = db_user[5] if db_user else 0
    limit_text = "∞" if is_premium(user.id) else "2"
    status     = get_status_text(user.id)
    await message.answer(
        f"👤 *Profil | Профиль*\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"🆔 ID: `{user.id}`\n"
        f"👤 Ism | Имя: {user.full_name}\n"
        f"📊 Status: {status}\n"
        f"📥 Bugun | Сегодня: {downloads}/{limit_text}\n"
        f"━━━━━━━━━━━━━━━━━━━━━",
        parse_mode="Markdown"
    )

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 📚 9. KITOB QIDIRUV TIZIMI
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@dp.message(F.text == "📚 Kitob | Книга")
async def cmd_ask_book(message: types.Message, state: FSMContext):
    register_user(message.from_user.id, message.from_user.username or "", message.from_user.full_name or "")
    allowed, _ = check_limit(message.from_user.id)
    if allowed:
        await message.answer(MSG["ask_book"], parse_mode="Markdown")
        await state.set_state(States.waiting_for_book)
    else:
        await message.answer(MSG["limit_out"], reply_markup=limit_keyboard(), parse_mode="Markdown")

@dp.message(States.waiting_for_book)
async def cmd_fetch_book(message: types.Message, state: FSMContext):
    await state.clear()
    query = message.text.strip()
    if not query:
        await message.answer("⚠️ Kitob nomini kiriting! | Введите название книги!")
        return

    status_msg  = await message.answer(MSG["searching"])
    query_param = requests.utils.quote(query)
    found       = []

    # ── Manba 1: Internet Archive ────────────────────────────────
    try:
        url = (
            f"https://archive.org/advancedsearch.php"
            f"?q=title:({query_param})+AND+mediatype:(texts)"
            f"&fl[]=identifier,title,creator&sort[]=downloads+desc&rows=5&output=json"
        )
        docs = requests.get(url, timeout=7).json().get("response", {}).get("docs", [])
        for doc in docs:
            ident = doc.get("identifier")
            if not ident:
                continue
            files = requests.get(f"https://archive.org/metadata/{ident}/files", timeout=5).json()
            for f in files.get("result", []):
                if f.get("name", "").endswith(".pdf"):
                    found.append({
                        "title":   doc.get("title", query),
                        "author":  doc.get("creator", "Noma'lum"),
                        "pdf_url": f"https://archive.org/download/{ident}/{requests.utils.quote(f['name'])}",
                        "source":  "Internet Archive"
                    })
                    break
            if found:
                break
    except Exception:
        pass

    # ── Manba 2: Open Library ────────────────────────────────────
    if not found:
        try:
            docs = requests.get(
                f"https://openlibrary.org/search.json?q={query_param}&limit=3",
                timeout=7
            ).json().get("docs", [])
            for book in docs:
                ol_id = (book.get("ia") or [None])[0]
                if ol_id:
                    found.append({
                        "title":   book.get("title", query),
                        "author":  (book.get("author_name") or ["Noma'lum"])[0],
                        "pdf_url": f"https://archive.org/download/{ol_id}/{ol_id}.pdf",
                        "source":  "Open Library"
                    })
                    break
        except Exception:
            pass

    # ── Manba 3: Google Books (zaxira havola) ────────────────────
    google_link = None
    try:
        items = requests.get(
            f"https://www.googleapis.com/books/v1/volumes?q={query_param}&maxResults=1",
            timeout=5
        ).json().get("items", [])
        if items:
            info   = items[0].get("volumeInfo", {})
            access = items[0].get("accessInfo", {})
            google_link = (
                access.get("pdf", {}).get("downloadLink")
                or info.get("previewLink")
            )
    except Exception:
        pass

    try:
        await status_msg.delete()
    except Exception:
        pass

    # ── Natija ───────────────────────────────────────────────────
    if found:
        best        = found[0]
        sending_msg = await message.answer(MSG["sending_pdf"])
        try:
            r = requests.get(best["pdf_url"], headers={"User-Agent": "Mozilla/5.0"}, timeout=30, stream=True)
            r.raise_for_status()
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                for chunk in r.iter_content(8192):
                    tmp.write(chunk)
                tmp_path = tmp.name
            increment_download(message.from_user.id)
            await sending_msg.delete()
            await bot.send_document(
                chat_id  = message.chat.id,
                document = FSInputFile(tmp_path, filename=f"{best['title'][:40]}.pdf"),
                caption  = (
                    f"✅ *{best['title']}*\n"
                    f"✍️ {best['author']}\n"
                    f"🌐 {best['source']}"
                ),
                parse_mode="Markdown"
            )
            os.unlink(tmp_path)
        except Exception:
            try:
                await sending_msg.delete()
            except Exception:
                pass
            btns = [[types.InlineKeyboardButton(text="📖 Ko'rish | Открыть", url=best["pdf_url"])]]
            if google_link:
                btns.append([types.InlineKeyboardButton(text="📚 Google Books", url=google_link)])
            await message.answer(
                MSG["big_file"],
                reply_markup=types.InlineKeyboardMarkup(inline_keyboard=btns),
                parse_mode="Markdown"
            )
            increment_download(message.from_user.id)
    elif google_link:
        await message.answer(
            "⚠️ PDF topilmadi, Google Books da mavjud:\n"
            "⚠️ PDF не найден, доступно в Google Books:",
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                types.InlineKeyboardButton(text="📚 Google Books", url=google_link)
            ]])
        )
    else:
        await message.answer(MSG["book_not_found"], parse_mode="Markdown")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🎧 10. AUDIO TIZIMI (edge-tts)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
VOICES = {
    "uz": "uz-UZ-SardorNeural",    # O'zbek
    "ru": "ru-RU-SvetlanaNeural",  # Rus
    "en": "en-US-AriaNeural",      # Ingliz
}

def detect_lang(text: str) -> str:
    """Matn tilinini aniqlash"""
    cyrillic = sum(1 for c in text if '\u0400' <= c <= '\u04FF')
    latin    = sum(1 for c in text if c.isascii() and c.isalpha())
    return "uz" if cyrillic >= latin else "en"

@dp.message(F.text == "🎧 Audio")
async def cmd_ask_audio(message: types.Message, state: FSMContext):
    register_user(message.from_user.id, message.from_user.username or "", message.from_user.full_name or "")
    allowed, _ = check_limit(message.from_user.id)
    if allowed:
        await message.answer(MSG["ask_audio"], parse_mode="Markdown")
        await state.set_state(States.waiting_for_audio)
    else:
        await message.answer(MSG["limit_out"], reply_markup=limit_keyboard(), parse_mode="Markdown")

@dp.message(States.waiting_for_audio)
async def cmd_generate_audio(message: types.Message, state: FSMContext):
    await state.clear()
    text = message.text.strip()
    if len(text) > 3000:
        await message.answer(MSG["text_too_long"])
        return
    status_msg = await message.answer(MSG["audio_making"])
    try:
        voice    = VOICES[detect_lang(text)]
        tmp_path = tempfile.mktemp(suffix=".mp3")
        await edge_tts.Communicate(text, voice).save(tmp_path)
        increment_download(message.from_user.id)
        await status_msg.delete()
        await bot.send_audio(
            chat_id   = message.chat.id,
            audio     = FSInputFile(tmp_path, filename="audio.mp3"),
            title     = text[:30] + "...",
            performer = "🧠 INTELLEKT Bot"
        )
        os.unlink(tmp_path)
    except Exception:
        try:
            await status_msg.edit_text(MSG["audio_error"])
        except Exception:
            pass

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 💎 11. PREMIUM — TELEGRAM STARS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PLANS = {
    "stars_1day":     {"label": "1 Kunlik | 1 День",      "stars": 50,  "plan": "1day"},
    "stars_1month":   {"label": "1 Oylik | 1 Месяц",      "stars": 200, "plan": "1month"},
    "stars_3month":   {"label": "3 Oylik | 3 Месяца",     "stars": 450, "plan": "3month"},
    "stars_lifetime": {"label": "💎 Umrbod | Пожизненно", "stars": 800, "plan": "lifetime"},
}

async def send_premium_menu(chat_id: int):
    """Premium menyu yuborish"""
    buttons = [
        [types.InlineKeyboardButton(
            text=f"{v['label']} — {v['stars']} ⭐",
            callback_data=f"buy_{k}"
        )]
        for k, v in PLANS.items()
    ]
    await bot.send_message(
        chat_id,
        MSG["premium_menu"],
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=buttons),
        parse_mode="Markdown"
    )

@dp.message(F.text == "💎 Premium")
async def cmd_premium(message: types.Message):
    await send_premium_menu(message.chat.id)

@dp.callback_query(F.data == "show_premium")
async def cb_show_premium(callback: types.CallbackQuery):
    await callback.answer()
    await send_premium_menu(callback.message.chat.id)

@dp.callback_query(F.data.startswith("buy_stars_"))
async def cb_buy_stars(callback: types.CallbackQuery):
    await callback.answer()
    key  = callback.data.replace("buy_", "")
    plan = PLANS.get(key)
    if not plan:
        return
    await bot.send_invoice(
        chat_id       = callback.message.chat.id,
        title         = f"💎 INTELLEKT — {plan['label']}",
        description   = f"✅ Cheksiz kitob va audio | Безлимитный доступ\n⭐ {plan['stars']} Stars",
        provider_token= "",        # Stars uchun bo'sh
        currency      = "XTR",    # Telegram Stars
        prices        = [LabeledPrice(label=plan["label"], amount=plan["stars"])],
        payload       = f"premium_{plan['plan']}_{callback.from_user.id}"
    )

@dp.pre_checkout_query()
async def pre_checkout(query: PreCheckoutQuery):
    await bot.answer_pre_checkout_query(query.id, ok=True)

@dp.message(F.successful_payment)
async def on_successful_payment(message: types.Message):
    # payload: "premium_1month_123456"
    parts   = message.successful_payment.invoice_payload.split("_")
    plan    = parts[1] if len(parts) > 1 else "1month"
    user_id = int(parts[2]) if len(parts) > 2 else message.from_user.id
    stars   = message.successful_payment.total_amount

    set_premium(user_id, plan)

    plan_labels = {
        "1day": "1 Kunlik | 1 День",
        "1month": "1 Oylik | 1 Месяц",
        "3month": "3 Oylik | 3 Месяца",
        "lifetime": "Umrbod | Пожизненно"
    }

    # Foydalanuvchiga xabar
    await message.answer(
        MSG["premium_success"] + f"\n\n📦 *{plan_labels.get(plan, plan)}*",
        parse_mode="Markdown"
    )

    # Adminga xabar
    if ADMIN_ID:
        try:
            await bot.send_message(
                ADMIN_ID,
                f"💰 *Yangi to'lov! | Новая оплата!*\n\n"
                f"👤 {message.from_user.full_name} (@{message.from_user.username})\n"
                f"🆔 ID: `{user_id}`\n"
                f"📦 Paket: {plan_labels.get(plan, plan)}\n"
                f"⭐ Stars: {stars}",
                parse_mode="Markdown"
            )
        except Exception:
            pass

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🛡 12. ADMIN BUYRUQLARI
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@dp.message(Command("addpremium"))
async def cmd_add_premium(message: types.Message):
    """Qo'lda premium berish: /addpremium [user_id] [plan]"""
    if message.from_user.id != ADMIN_ID:
        return
    parts = message.text.split()
    if len(parts) != 3:
        await message.answer(
            "📌 Ishlatish | Использование:\n"
            "`/addpremium [user_id] [1day|1month|3month|lifetime]`",
            parse_mode="Markdown"
        )
        return
    try:
        uid, plan = int(parts[1]), parts[2]
        register_user(uid, "", "")
        set_premium(uid, plan)
        await message.answer(f"✅ {uid} ga `{plan}` premium berildi!", parse_mode="Markdown")
        await bot.send_message(
            uid,
            f"🎁 *Admindan sovg'a!*\n*{plan}* Premium faollashdi! 🎉",
            parse_mode="Markdown"
        )
    except Exception as e:
        await message.answer(f"❌ Xatolik: `{e}`", parse_mode="Markdown")

@dp.message(Command("delpremium"))
async def cmd_del_premium(message: types.Message):
    """Premiumni olib tashlash: /delpremium [user_id]"""
    if message.from_user.id != ADMIN_ID:
        return
    parts = message.text.split()
    if len(parts) != 2:
        await message.answer("`/delpremium [user_id]`", parse_mode="Markdown")
        return
    try:
        uid = int(parts[1])
        cursor.execute("UPDATE users SET premium_type = NULL, premium_until = NULL WHERE user_id = ?", (uid,))
        conn.commit()
        await message.answer(f"✅ {uid} dan premium olindi!")
    except Exception as e:
        await message.answer(f"❌ Xatolik: `{e}`", parse_mode="Markdown")

@dp.message(Command("stats"))
async def cmd_stats(message: types.Message):
    """Bot statistikasi"""
    if message.from_user.id != ADMIN_ID:
        return
    cursor.execute("SELECT COUNT(*) FROM users")
    total = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM users WHERE premium_type IS NOT NULL")
    prem  = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM users WHERE joined_date = ?", (datetime.today().strftime('%Y-%m-%d'),))
    today_new = cursor.fetchone()[0]
    await message.answer(
        f"📊 *Statistika | Статистика*\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"👥 Jami | Всего: *{total}*\n"
        f"💎 Premium: *{prem}*\n"
        f"🆓 Bepul | Бесплатно: *{total - prem}*\n"
        f"🆕 Bugun | Сегодня: *{today_new}*\n"
        f"━━━━━━━━━━━━━━━━━━━━━",
        parse_mode="Markdown"
    )

@dp.message(Command("broadcast"))
async def cmd_broadcast(message: types.Message):
    """Barcha foydalanuvchilarga xabar: /broadcast [matn]"""
    if message.from_user.id != ADMIN_ID:
        return
    text = message.text.replace("/broadcast", "").strip()
    if not text:
        await message.answer("📌 `/broadcast [xabar matni]`", parse_mode="Markdown")
        return
    cursor.execute("SELECT user_id FROM users")
    users     = cursor.fetchall()
    sent      = 0
    failed    = 0
    status    = await message.answer(f"📤 Yuborilmoqda... | Отправка... (0/{len(users)})")
    for i, (uid,) in enumerate(users):
        try:
            await bot.send_message(uid, f"📢 *INTELLEKT:*\n\n{text}", parse_mode="Markdown")
            sent += 1
        except Exception:
            failed += 1
        if (i + 1) % 10 == 0:
            try:
                await status.edit_text(f"📤 Yuborilmoqda... ({i+1}/{len(users)})")
            except Exception:
                pass
        await asyncio.sleep(0.05)
    await status.edit_text(
        f"✅ Xabar yuborildi!\n\n"
        f"📨 Yuborildi | Отправлено: {sent}\n"
        f"❌ Xatolik | Ошибка: {failed}"
    )

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🌐 13. RENDER HEALTH CHECK
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"INTELLEKT Bot is alive!")
    def log_message(self, *args):
        pass  # Loglarni yashirish

def run_health_server():
    port = int(os.environ.get("PORT", 10000))
    HTTPServer(('0.0.0.0', port), HealthHandler).serve_forever()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ▶️ 14. ISHGA TUSHIRISH
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
if __name__ == "__main__":
    threading.Thread(target=run_health_server, daemon=True).start()
    print("━" * 50)
    print("🤖 INTELLEKT Bot ishga tushdi!")
    print("━" * 50)
    asyncio.run(dp.run_polling(bot))
