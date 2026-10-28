import asyncio
import logging
import os

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.types import (
    Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
)
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("hashtag_ai")

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
CHANNEL_ID = os.getenv("CHANNEL_ID", "@o11abu").strip()
WEBAPP_URL = os.getenv("WEBAPP_URL", "").strip()

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN yo‘q. Render > Environment bo‘limida BOT_TOKEN qo‘shing.")

bot = Bot(BOT_TOKEN)
dp = Dispatcher()

DIRECTIONS = [
    ("🎬 Kino", "kino"), ("🎨 Multfilm", "multfilm"),
    ("🤖 AI", "ai"), ("😂 Vayn", "vayn"),
    ("🏫 School", "school"), ("👤 Shaxsiy blog", "blog"),
    ("🌙 Arabic", "arabic"), ("🎵 Musiqa", "music"),
    ("⭐ Fan club", "fanclub"), ("🕌 Islomiy", "islamic"),
    ("🎞 iMovie", "imovie"), ("❤️ Love", "love"),
    ("📱 Stories", "stories"), ("✨ Edit", "edit"),
    ("⚽ Futbol", "football"), ("💌 Atalgan video", "dedicated"),
]

def main_keyboard():
    rows = [
        [KeyboardButton(text="🔥 TOP hashtaglar"), KeyboardButton(text="🤖 AI hashtag yaratish")],
        [KeyboardButton(text="🎬 Video analiz")],
    ]
    if WEBAPP_URL:
        rows.append([KeyboardButton(text="📱 Kabinet", web_app=WebAppInfo(url=WEBAPP_URL))])
    else:
        rows.append([KeyboardButton(text="📱 Kabinet")])
    rows.append([KeyboardButton(text="ℹ️ Yordam")])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)

def sub_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Kanalga obuna bo‘lish", url="https://t.me/o11abu")],
        [InlineKeyboardButton(text="✅ Obunani tekshirish", callback_data="check_sub")],
    ])

async def is_subscribed(user_id):
    try:
        member = await bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in ("member", "administrator", "creator")
    except (TelegramBadRequest, TelegramForbiddenError) as e:
        log.warning("Obunani tekshirib bo‘lmadi: %s", e)
        return False

async def allowed(message):
    if not message.from_user:
        return False
    if await is_subscribed(message.from_user.id):
        return True
    await message.answer("🔒 Botdan foydalanish uchun avval @o11abu kanaliga obuna bo‘ling.", reply_markup=sub_keyboard())
    return False

@dp.message(CommandStart())
async def start(message: Message):
    if not await allowed(message):
        return
    await message.answer(
        "👋 Assalomu alaykum! Hashtag AI botiga xush kelibsiz!\n\n"
        "🚀 Reels hashtaglari, trend tahlili va video analiz uchun menyudan tanlang.",
        reply_markup=main_keyboard()
    )

@dp.callback_query(F.data == "check_sub")
async def check_sub(callback: CallbackQuery):
    if await is_subscribed(callback.from_user.id):
        await callback.message.answer("✅ Obuna tasdiqlandi!", reply_markup=main_keyboard())
        await callback.answer("Tasdiqlandi")
    else:
        await callback.answer("Avval @o11abu kanaliga obuna bo‘ling.", show_alert=True)

@dp.message(Command("help"))
@dp.message(F.text == "ℹ️ Yordam")
async def help_handler(message: Message):
    if await allowed(message):
        await message.answer(
            "ℹ️ Asosiy menyudan bo‘lim tanlang. Eslatma: haqiqiy Instagram TOP-3 statistikasi "
            "uchun sana, caption va ko‘rishlar sonini beradigan alohida ruxsat etilgan manba kerak.",
            reply_markup=main_keyboard()
        )

async def show_directions(message, mode):
    rows, row = [], []
    for label, key in DIRECTIONS:
        row.append(InlineKeyboardButton(text=label, callback_data=f"dir:{mode}:{key}"))
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([InlineKeyboardButton(text="⬅️ Orqaga", callback_data="back")])
    await message.answer("🧭 Yo‘nalishni tanlang:", reply_markup=InlineKeyboardMarkup(inline_keyboard=rows))

@dp.message(F.text == "🔥 TOP hashtaglar")
async def top_handler(message: Message):
    if await allowed(message):
        await show_directions(message, "top")

@dp.message(F.text == "🤖 AI hashtag yaratish")
async def gen_handler(message: Message):
    if await allowed(message):
        await show_directions(message, "gen")

@dp.message(F.text == "🎬 Video analiz")
async def video_handler(message: Message):
    if await allowed(message):
        await show_directions(message, "video")

@dp.callback_query(F.data == "back")
async def back_handler(callback: CallbackQuery):
    await callback.message.answer("🏠 Asosiy menyu", reply_markup=main_keyboard())
    await callback.answer()

@dp.callback_query(F.data.startswith("dir:"))
async def direction_handler(callback: CallbackQuery):
    if not await is_subscribed(callback.from_user.id):
        await callback.message.answer("🔒 Avval @o11abu kanaliga obuna bo‘ling.", reply_markup=sub_keyboard())
        await callback.answer()
        return
    _, mode, key = callback.data.split(":")
    label = next((x for x, k in DIRECTIONS if k == key), key)
    if mode == "top":
        text = f"🔥 {label} tanlandi.\n\nHaqiqiy TOP-3 uchun Instagram’dagi so‘nggi 7 kunlik sana, caption va ko‘rishlar sonini beradigan manba ulanishi kerak. Bu boshlang‘ich fayl hali tashqi ma’lumot manbasini ulamaydi."
    elif mode == "gen":
        text = f"🤖 {label} tanlandi. Endi mavzuni yozing.\n\nAI generatori uchun alohida model yoki API ulanishi kerak."
    else:
        text = f"🎬 {label} tanlandi. Endi videoni chatga yuboring. To‘liq texnik tahlil uchun video analiz modulini ulash kerak."
    await callback.message.answer(text)
    await callback.answer()

@dp.message(F.video)
async def video_received(message: Message):
    if await allowed(message):
        await message.answer("🎬 Video qabul qilindi. To‘liq hook, FPS, rezolyutsiya va audio tahlili uchun video analiz moduli ulanishi kerak.")

@dp.message(F.text == "📱 Kabinet")
async def cabinet_handler(message: Message):
    if not await allowed(message):
        return
    if WEBAPP_URL:
        await message.answer("📱 Kabinetni oching:", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Kabinetni ochish", web_app=WebAppInfo(url=WEBAPP_URL))]
        ]))
    else:
        await message.answer("⚙️ Kabinet hali ulanmagan. Render Environment’da WEBAPP_URL uchun HTTPS manzil kiriting.")

@dp.message()
async def fallback(message: Message):
    if await allowed(message):
        await message.answer("Menyudagi tugmalardan foydalaning yoki /start yuboring.", reply_markup=main_keyboard())

async def main():
    log.info("Hashtag AI bot ishga tushmoqda")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
