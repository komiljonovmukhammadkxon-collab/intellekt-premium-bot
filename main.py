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

from bs4 import BeautifulSoup
from fpdf import FPDF
from gtts import gTTS
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import LabeledPrice, PreCheckoutQuery, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🔑 1. TOKENLAR
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
BOT_TOKEN = os.environ.get("BOT_TOKEN", "TOKENINGIZNI_BU_YERGA_YOZING")
ADMIN_ID  = int(os.environ.get("ADMIN_ID", "0"))

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 💬 2. XABARLAR MATNI
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
        "💡 O'zbek, Rus yoki Inglizcha yozing\n"
        "💡 Пишите на узбекском, русском или английском"
    ),
    "searching":    "⏳ Qidirilmoqda... | Идёт поиск...",
    "sending_pdf":  "📤 PDF yuklanmoqda... | Загрузка PDF...",
    "making_pdf":   "📄 PDF tayyorlanmoqda... | Создание PDF...",
    "book_not_found": (
        "❌ *Kitob topilmadi*\n"
        "❌ *Книга не найдена*\n\n"
        "💡 Maslahat | Совет:\n"
        "• To'liq nom yozing | Пишите полное название\n"
        "• Muallif nomini qo'shing | Добавьте автора\n"
        "• Misol: `Abdulla Qahhor` yoki `Atomic Habits`"
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
        user_id            INTEGER PRIMARY KEY,
        username           TEXT,
        full_name          TEXT,
        premium_type       TEXT    DEFAULT NULL,
        premium_until      TEXT    DEFAULT NULL,
        downloads_today    INTEGER DEFAULT 0,
        last_download_date TEXT,
        joined_date        TEXT
    )
""")
conn.commit()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🔧 5. YORDAMCHI FUNKSIYALAR
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def register_user(user_id, username, full_name):
    today = datetime.today().strftime('%Y-%m-%d')
    cursor.execute("""
        INSERT OR IGNORE INTO users
        (user_id, username, full_name, last_download_date, joined_date)
        VALUES (?, ?, ?, ?, ?)
    """, (user_id, username, full_name, today, today))
    conn.commit()

def get_user(user_id):
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    return cursor.fetchone()

def is_premium(user_id):
    user = get_user(user_id)
    if not user:
        return False
    ptype, puntil = user[3], user[4]
    if ptype == "lifetime":
        return True
    if puntil:
        return datetime.today() <= datetime.strptime(puntil, '%Y-%m-%d')
    return False

def set_premium(user_id, plan):
    today = datetime.today()
    durations = {"1day": 1, "1month": 30, "3month": 90}
    until = None if plan == "lifetime" else (today + timedelta(days=durations.get(plan, 30))).strftime('%Y-%m-%d')
    cursor.execute("UPDATE users SET premium_type = ?, premium_until = ? WHERE user_id = ?", (plan, until, user_id))
    conn.commit()

def check_limit(user_id):
    if is_premium(user_id):
        return True, "premium"
    user = get_user(user_id)
    if not user:
        return True, "free"
    today = datetime.today().strftime('%Y-%m-%d')
    downloads, last_date = user[5], user[6]
    if last_date != today:
        cursor.execute("UPDATE users SET downloads_today = 0, last_download_date = ? WHERE user_id = ?", (today, user_id))
        conn.commit()
        downloads = 0
    return (True, "free") if downloads < 2 else (False, "limit_out")

def increment_download(user_id):
    if not is_premium(user_id):
        cursor.execute("UPDATE users SET downloads_today = downloads_today + 1 WHERE user_id = ?", (user_id,))
        conn.commit()

def get_status_text(user_id):
    user = get_user(user_id)
    if not user:
        return "🆓 Bepul | Бесплатно"
    ptype, puntil = user[3], user[4]
    if ptype == "lifetime":
        return "💎 Umrbod Premium | Пожизненный Premium"
    if puntil and datetime.today() <= datetime.strptime(puntil, '%Y-%m-%d'):
        days_left = (datetime.strptime(puntil, '%Y-%m-%d') - datetime.today()).days
        labels = {"1day": "Kunlik|Дневной", "1month": "Oylik|Месячный", "3month": "3 Oylik|3 Месяца"}
        return f"✅ {labels.get(ptype, 'Premium')} — {days_left} kun | дней qoldi"
    return "🆓 Bepul | Бесплатно (kuniga 2 ta | 2 в день)"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🎹 6. KLAVIATURALAR
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def main_keyboard():
    return types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="📚 Kitob | Книга"), types.KeyboardButton(text="🎧 Audio")],
            [types.KeyboardButton(text="💎 Premium"),       types.KeyboardButton(text="👤 Profil | Профиль")],
        ],
        resize_keyboard=True
    )

def limit_keyboard():
    return types.InlineKeyboardMarkup(inline_keyboard=[[
        types.InlineKeyboardButton(text="💎 Premium olish | Купить Premium", callback_data="show_premium")
    ]])

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🚀 7. /START
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
    db_user    = get_user(user.id)
    downloads  = db_user[5] if db_user else 0
    limit_text = "∞" if is_premium(user.id) else "2"
    await message.answer(
        f"👤 *Profil | Профиль*\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"🆔 ID: `{user.id}`\n"
        f"👤 Ism | Имя: {user.full_name}\n"
        f"📊 Status: {get_status_text(user.id)}\n"
        f"📥 Bugun | Сегодня: {downloads}/{limit_text}\n"
        f"━━━━━━━━━━━━━━━━━━━━━",
        parse_mode="Markdown"
    )

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 📚 9. KITOB QIDIRUV
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

def make_pdf_from_text(title, text):
    """Matndan PDF yasash — Unicode shrift bilan"""
    pdf = FPDF()
    pdf.add_page()

    # DejaVu shrift (Unicode, O'zbek/Rus harflarini ko'rsatadi)
    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    if os.path.exists(font_path):
        pdf.add_font("DejaVu", "", font_path, uni=True)
        pdf.set_font("DejaVu", size=15)
    else:
        pdf.set_font("Helvetica", size=15)

    # Sarlavha
    pdf.set_fill_color(30, 30, 30)
    pdf.multi_cell(0, 12, title, align="C")
    pdf.ln(6)

    # Matn
    if os.path.exists(font_path):
        pdf.set_font("DejaVu", size=11)
    else:
        pdf.set_font("Helvetica", size=11)

    for line in text.split("\n"):
        line = line.strip()
        if not line:
            pdf.ln(3)
            continue
        try:
            pdf.multi_cell(0, 7, line)
        except Exception:
            pass

    tmp = tempfile.mktemp(suffix=".pdf")
    pdf.output(tmp)
    return tmp

def search_ziyouz(query):
    """Ziyouz.com dan matn olish"""
    try:
        url = f"https://ziyouz.com/?s={requests.utils.quote(query)}"
        r   = requests.get(url, timeout=10, headers=HEADERS)
        soup = BeautifulSoup(r.text, "html.parser")

        links = soup.select("h2.entry-title a") or soup.select("h1.entry-title a") or soup.select("article a")
        if not links:
            return None

        book_url = links[0]["href"]
        r2   = requests.get(book_url, timeout=10, headers=HEADERS)
        soup2 = BeautifulSoup(r2.text, "html.parser")

        content = (
            soup2.select_one("div.entry-content") or
            soup2.select_one("div.post-content") or
            soup2.select_one("article")
        )
        if not content:
            return None

        title_tag  = soup2.select_one("h1.entry-title") or soup2.select_one("h1")
        title_text = title_tag.get_text(strip=True) if title_tag else query
        text       = content.get_text(separator="\n", strip=True)

        if len(text) < 200:
            return None

        return {"title": title_text, "text": text[:60000], "source": "Ziyouz.com"}
    except Exception:
        return None

def search_kutubxona(query):
    """Kutubxona.uz dan matn olish"""
    try:
        url  = f"https://kutubxona.uz/?s={requests.utils.quote(query)}"
        r    = requests.get(url, timeout=10, headers=HEADERS)
        soup = BeautifulSoup(r.text, "html.parser")

        links = soup.select("h2.entry-title a") or soup.select("h2 a")
        if not links:
            return None

        book_url = links[0]["href"]
        r2   = requests.get(book_url, timeout=10, headers=HEADERS)
        soup2 = BeautifulSoup(r2.text, "html.parser")

        content = soup2.select_one("div.entry-content") or soup2.select_one("article")
        if not content:
            return None

        title_tag  = soup2.select_one("h1")
        title_text = title_tag.get_text(strip=True) if title_tag else query
        text       = content.get_text(separator="\n", strip=True)

        if len(text) < 200:
            return None

        return {"title": title_text, "text": text[:60000], "source": "Kutubxona.uz"}
    except Exception:
        return None

def search_archive(query):
    """Internet Archive dan PDF qidirish"""
    try:
        qp   = requests.utils.quote(query)
        url  = (
            f"https://archive.org/advancedsearch.php"
            f"?q=title:({qp})+AND+mediatype:(texts)"
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
                    return {
                        "title":   doc.get("title", query),
                        "author":  doc.get("creator", "Noma'lum"),
                        "pdf_url": f"https://archive.org/download/{ident}/{requests.utils.quote(f['name'])}",
                        "source":  "Internet Archive"
                    }
    except Exception:
        pass
    return None

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

    status_msg = await message.answer(MSG["searching"])

    # ── 1. Ziyouz.com ────────────────────────────────────────────
    result = await asyncio.get_event_loop().run_in_executor(None, search_ziyouz, query)

    # ── 2. Kutubxona.uz ──────────────────────────────────────────
    if not result:
        result = await asyncio.get_event_loop().run_in_executor(None, search_kutubxona, query)

    # ── Matndan PDF yasash ────────────────────────────────────────
    if result:
        try:
            await status_msg.edit_text(MSG["making_pdf"])
            tmp_path = await asyncio.get_event_loop().run_in_executor(
                None, make_pdf_from_text, result["title"], result["text"]
            )
            await status_msg.delete()
            increment_download(message.from_user.id)
            await bot.send_document(
                chat_id  = message.chat.id,
                document = FSInputFile(tmp_path, filename=f"{result['title'][:40]}.pdf"),
                caption  = f"✅ *{result['title']}*\n🌐 {result['source']}",
                parse_mode="Markdown"
            )
            os.unlink(tmp_path)
            return
        except Exception:
            pass

    # ── 3. Internet Archive (inglizcha kitoblar) ──────────────────
    arch = await asyncio.get_event_loop().run_in_executor(None, search_archive, query)
    if arch:
        try:
            await status_msg.edit_text(MSG["sending_pdf"])
            r = requests.get(arch["pdf_url"], headers=HEADERS, timeout=30, stream=True)
            r.raise_for_status()
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                for chunk in r.iter_content(8192):
                    tmp.write(chunk)
                tmp_path = tmp.name
            increment_download(message.from_user.id)
            await status_msg.delete()
            await bot.send_document(
                chat_id  = message.chat.id,
                document = FSInputFile(tmp_path, filename=f"{arch['title'][:40]}.pdf"),
                caption  = f"✅ *{arch['title']}*\n✍️ {arch['author']}\n🌐 Internet Archive",
                parse_mode="Markdown"
            )
            os.unlink(tmp_path)
            return
        except Exception:
            try:
                await status_msg.delete()
            except Exception:
                pass
            await message.answer(
                MSG["big_file"],
                reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                    types.InlineKeyboardButton(text="📖 Ko'rish | Открыть", url=arch["pdf_url"])
                ]])
            )
            increment_download(message.from_user.id)
            return

    # ── Topilmadi ────────────────────────────────────────────────
    try:
        await status_msg.delete()
    except Exception:
        pass
    await message.answer(MSG["book_not_found"], parse_mode="Markdown")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🎧 10. AUDIO TIZIMI (gTTS)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def detect_lang(text):
    cyrillic = sum(1 for c in text if '\u0400' <= c <= '\u04FF')
    latin    = sum(1 for c in text if c.isascii() and c.isalpha())
    if cyrillic > latin:
        # Ko'proq kirill → O'zbek yoki Rus
        # Rus harflari (ы, э, ъ) bo'lsa — Rus
        rus_chars = sum(1 for c in text if c in 'ыэъёЫЭЪЁ')
        return "ru" if rus_chars > 0 else "uz"
    return "en"

GTTS_LANG = {"uz": "uz", "ru": "ru", "en": "en"}

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
        lang     = detect_lang(text)
        gtts_lang = GTTS_LANG.get(lang, "en")
        tmp_path = tempfile.mktemp(suffix=".mp3")

        def make_audio():
            tts = gTTS(text=text, lang=gtts_lang, slow=False)
            tts.save(tmp_path)

        await asyncio.get_event_loop().run_in_executor(None, make_audio)
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

async def send_premium_menu(chat_id):
    buttons = [
        [types.InlineKeyboardButton(text=f"{v['label']} — {v['stars']} ⭐", callback_data=f"buy_{k}")]
        for k, v in PLANS.items()
    ]
    await bot.send_message(chat_id, MSG["premium_menu"],
                           reply_markup=types.InlineKeyboardMarkup(inline_keyboard=buttons),
                           parse_mode="Markdown")

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
        chat_id        = callback.message.chat.id,
        title          = f"💎 INTELLEKT — {plan['label']}",
        description    = f"✅ Cheksiz kitob va audio | Безлимитный доступ\n⭐ {plan['stars']} Stars",
        provider_token = "",
        currency       = "XTR",
        prices         = [LabeledPrice(label=plan["label"], amount=plan["stars"])],
        payload        = f"premium_{plan['plan']}_{callback.from_user.id}"
    )

@dp.pre_checkout_query()
async def pre_checkout(query: PreCheckoutQuery):
    await bot.answer_pre_checkout_query(query.id, ok=True)

@dp.message(F.successful_payment)
async def on_successful_payment(message: types.Message):
    parts   = message.successful_payment.invoice_payload.split("_")
    plan    = parts[1] if len(parts) > 1 else "1month"
    user_id = int(parts[2]) if len(parts) > 2 else message.from_user.id
    stars   = message.successful_payment.total_amount
    set_premium(user_id, plan)
    plan_labels = {
        "1day": "1 Kunlik | 1 День", "1month": "1 Oylik | 1 Месяц",
        "3month": "3 Oylik | 3 Месяца", "lifetime": "Umrbod | Пожизненно"
    }
    await message.answer(MSG["premium_success"] + f"\n\n📦 *{plan_labels.get(plan, plan)}*", parse_mode="Markdown")
    if ADMIN_ID:
        try:
            await bot.send_message(
                ADMIN_ID,
                f"💰 *Yangi to'lov!*\n\n"
                f"👤 {message.from_user.full_name} (@{message.from_user.username})\n"
                f"🆔 `{user_id}`\n📦 {plan_labels.get(plan, plan)}\n⭐ {stars}",
                parse_mode="Markdown"
            )
        except Exception:
            pass

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🛡 12. ADMIN BUYRUQLARI
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@dp.message(Command("addpremium"))
async def cmd_add_premium(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    parts = message.text.split()
    if len(parts) != 3:
        await message.answer("`/addpremium [user_id] [1day|1month|3month|lifetime]`", parse_mode="Markdown")
        return
    try:
        uid, plan = int(parts[1]), parts[2]
        register_user(uid, "", "")
        set_premium(uid, plan)
        await message.answer(f"✅ {uid} ga `{plan}` premium berildi!", parse_mode="Markdown")
        await bot.send_message(uid, f"🎁 *Admindan sovg'a!*\n*{plan}* Premium faollashdi! 🎉", parse_mode="Markdown")
    except Exception as e:
        await message.answer(f"❌ Xatolik: `{e}`", parse_mode="Markdown")

@dp.message(Command("delpremium"))
async def cmd_del_premium(message: types.Message):
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
    if message.from_user.id != ADMIN_ID:
        return
    cursor.execute("SELECT COUNT(*) FROM users")
    total = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM users WHERE premium_type IS NOT NULL")
    prem  = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM users WHERE joined_date = ?", (datetime.today().strftime('%Y-%m-%d'),))
    today_new = cursor.fetchone()[0]
    await message.answer(
        f"📊 *Statistika*\n\n━━━━━━━━━━━━━━━━━━━━━\n"
        f"👥 Jami: *{total}*\n💎 Premium: *{prem}*\n"
        f"🆓 Bepul: *{total - prem}*\n🆕 Bugun: *{today_new}*\n"
        f"━━━━━━━━━━━━━━━━━━━━━",
        parse_mode="Markdown"
    )

@dp.message(Command("broadcast"))
async def cmd_broadcast(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    text = message.text.replace("/broadcast", "").strip()
    if not text:
        await message.answer("`/broadcast [xabar matni]`", parse_mode="Markdown")
        return
    cursor.execute("SELECT user_id FROM users")
    users  = cursor.fetchall()
    sent   = failed = 0
    status = await message.answer(f"📤 Yuborilmoqda... (0/{len(users)})")
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
    await status.edit_text(f"✅ Tayyor!\n📨 Yuborildi: {sent}\n❌ Xatolik: {failed}")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🌐 13. RENDER HEALTH CHECK
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"INTELLEKT Bot is alive!")
    def log_message(self, *args):
        pass

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
