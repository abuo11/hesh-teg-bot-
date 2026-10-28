from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from bot.config import settings
from bot.keyboards.inline import admin_kb
from bot.loader import repo
from bot.utils.text_formatter import esc

router = Router()


def _is_admin(uid: int) -> bool:
    return uid in settings.admin_ids


async def _render() -> str:
    s = await repo.stats()
    src = "\n".join(
        f"• {esc(r['source'])}: {r['ok']}/{r['total']} muvaffaqiyatli" for r in s["sources"]
    ) or "• ma’lumot yo‘q"
    return (
        "🛠 <b>Admin panel</b>\n\n"
        f"👥 Jami foydalanuvchilar: {s['users_total']}\n"
        f"🟢 Faol (7 kun): {s['users_active_7d']}\n"
        f"📅 Bugun faol: {s['users_today']} · amallar: {s['actions_today']}\n\n"
        f"🔥 TOP tahlillar: {s['top_total']}\n"
        f"🤖 AI generator: {s['gen_total']}\n"
        f"🎬 Video analizlar: {s['video_total']}\n"
        f"⚠️ API xatolari (7 kun): {s['api_errors_7d']}\n\n"
        f"<b>Ma’lumot manbalari (7 kun):</b>\n{src}"
    )


@router.message(Command("admin"))
async def admin(m: Message):
    if not _is_admin(m.from_user.id):
        return  # oddiy foydalanuvchiga ko'rsatilmaydi
    await m.answer(await _render(), reply_markup=admin_kb())


@router.callback_query(F.data == "admin:refresh")
async def refresh(c: CallbackQuery):
    if not _is_admin(c.from_user.id):
        await c.answer()
        return
    await c.message.edit_text(await _render(), reply_markup=admin_kb())
    await c.answer("Yangilandi")
