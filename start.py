from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.keyboards import reply as R
from bot.keyboards.inline import directions_kb
from bot.keyboards.webapp import cabinet_kb
from bot.keyboards.reply import main_menu

router = Router()

WELCOME = (
    "👋 Assalomu alaykum! Hashtag AI botiga xush kelibsiz!\n\n"
    "🚀 Instagram Reels uchun trend tahlili, original hashtaglar va video analiz bir joyda."
)
HELP = (
    "ℹ️ <b>Yordam</b>\n\n"
    "🔥 <b>TOP hashtaglar</b> — yo‘nalishni tanlab, oxirgi 7 kunlik TOP videolarni ko‘ring.\n"
    "🤖 <b>AI hashtag yaratish</b> — mavzu bo‘yicha caption va hashtag oling.\n"
    "🎬 <b>Video analiz</b> — videongizni yuboring, texnik tahlil oling.\n"
    "📱 <b>Kabinet</b> — Reels havolasidan caption, bio va History.\n\n"
    "Tayyor natijalar History bo‘limida avtomatik saqlanadi."
)


@router.message(CommandStart())
async def start(m: Message, state: FSMContext):
    await state.clear()
    await m.answer(WELCOME, reply_markup=main_menu())
    kb = cabinet_kb()
    await m.answer("📱 Kabinetni quyidagi tugma orqali oching:" if kb else
                   "📱 Kabinet hali sozlanmagan (WEBAPP_URL .env da HTTPS manzil bo‘lishi kerak).",
                   reply_markup=kb)


@router.message(Command("help"))
@router.message(F.text == R.BTN_HELP)
async def help_(m: Message):
    await m.answer(HELP)


@router.message(F.text == R.BTN_CAB)
async def cabinet(m: Message):
    kb = cabinet_kb()
    if kb:
        await m.answer("📱 Kabinet:", reply_markup=kb)
    else:
        await m.answer("⚠️ Kabinet sozlanmagan: .env faylida WEBAPP_URL (https://...) ni kiriting.")


@router.message(F.text.in_({R.BTN_TOP, R.BTN_GEN}))
async def directions(m: Message, state: FSMContext):
    await state.clear()
    await m.answer("📂 Yo‘nalishni tanlang:", reply_markup=directions_kb("menu"))


@router.callback_query(F.data == "back:main")
async def back_main(c: CallbackQuery, state: FSMContext):
    await state.clear()
    await c.message.answer("🏠 Bosh menyu", reply_markup=main_menu())
    await c.answer()


@router.callback_query(F.data == "back:dirs")
async def back_dirs(c: CallbackQuery):
    await c.message.edit_text("📂 Yo‘nalishni tanlang:", reply_markup=directions_kb("menu"))
    await c.answer()
