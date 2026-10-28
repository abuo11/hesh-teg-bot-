from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from bot.keyboards.webapp import cabinet_kb
from bot.loader import repo
from bot.utils.text_formatter import esc, short

router = Router()


@router.message(Command("history"))
async def history_cmd(m: Message):
    items, total = await repo.list_history(m.from_user.id, 0, 5)
    if not items:
        await m.answer("🕘 Hozircha tarix bo‘sh\n\nHashtag natijalaringiz shu yerda avtomatik saqlanadi.",
                       reply_markup=cabinet_kb())
        return
    lines = [f"🕘 <b>Oxirgi natijalar</b> (jami: {total})", ""]
    for it in items:
        lines.append(f"• {it['created_at'][:16].replace('T', ' ')} · {esc(it['result_type'])} · "
                     f"{esc(short(it['caption'] or ' '.join(it['hashtags']), 60))}")
    lines.append("\nTo‘liq tarix — kabinetning History bo‘limida.")
    await m.answer("\n".join(lines), reply_markup=cabinet_kb())
