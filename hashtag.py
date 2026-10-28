from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.keyboards.inline import (after_top_kb, direction_actions_kb, directions_kb, skip_kb, top_item_kb)
from bot.loader import ig, repo
from bot.services.directions import get_direction
from bot.services.instagram_api import SourceError
from bot.services.trend_analyzer import top_videos
from bot.utils.logger import logger
from bot.utils.text_formatter import esc, fmt_num, short, split_message, with_signature
from bot.utils.time_utils import fmt_dt

router = Router()


@router.callback_query(F.data.regexp(r"^dir:menu:\d+$"))
async def pick_direction(c: CallbackQuery, state: FSMContext):
    idx = int(c.data.split(":")[2])
    d = get_direction(idx)
    await state.update_data(dir_idx=idx)
    await c.message.edit_text(f"{d.emoji} <b>{esc(d.name)}</b>\nNima qilamiz?", reply_markup=direction_actions_kb(idx))
    await c.answer()


@router.callback_query(F.data.regexp(r"^top:\d+$"))
async def top(c: CallbackQuery, state: FSMContext):
    idx = int(c.data.split(":")[1])
    d = get_direction(idx)
    await c.answer()
    wait = await c.message.answer("⏳ Tahlil qilinmoqda...")
    await repo.bump("top")
    try:
        res = await top_videos(ig, d)
        await repo.log_api("instagram_graph", True)
    except SourceError as e:
        await repo.log_api("instagram_graph", False, str(e))
        await wait.edit_text(f"⚠️ Ma’lumot olinmadi.\n<i>{esc(str(e))}</i>",
                             reply_markup=direction_actions_kb(idx))
        return
    except Exception as e:  # kutilmagan xato
        logger.exception("top xatosi")
        await repo.log_api("instagram_graph", False, e.__class__.__name__)
        await wait.edit_text("⚠️ Kutilmagan xato yuz berdi. Qayta urinib ko‘ring.",
                             reply_markup=direction_actions_kb(idx))
        return

    if not res.items:
        await wait.edit_text(
            f"😕 Oxirgi 7 kun ichida «{esc(d.name)}» yo‘nalishi bo‘yicha mos video topilmadi "
            f"(tekshirildi: {res.scanned} ta).", reply_markup=direction_actions_kb(idx))
        return

    await wait.edit_text(f"🔥 <b>{esc(d.name)}</b> — oxirgi 7 kun\n<i>{esc(res.note)}</i>")
    stored, ids = [], []
    for i, m in enumerate(res.items):
        metric = m.views if res.metric_label == "ko‘rishlar" else m.likes
        hid = await repo.add_history(
            c.from_user.id, "top3", m.caption, m.hashtags, m.url, m.timestamp.isoformat() if m.timestamp else None,
            m.views, res.metric_label, m.source, d.name)
        ids.append(hid)
        stored.append({"caption": m.caption, "tags": m.hashtags, "url": m.url})
        body = (f"<b>#{i + 1}</b> · 📅 {fmt_dt(m.timestamp)} · 👁 {fmt_num(metric)} {res.metric_label}\n\n"
                f"{esc(short(m.caption, 500))}\n\n{esc(' '.join(m.hashtags))}\n\n\n{esc(with_signature('').strip())}")
        await c.message.answer(body[:4000], reply_markup=top_item_kb(i, m.url), disable_web_page_preview=True)
    await state.update_data(top=stored, top_ids=ids)
    await c.message.answer("Natijalar History bo‘limiga avtomatik saqlandi.", reply_markup=after_top_kb())


@router.callback_query(F.data.regexp(r"^cp:top:(cap|tags):\d+$"))
async def copy_top(c: CallbackQuery, state: FSMContext):
    _, _, kind, i = c.data.split(":")
    data = (await state.get_data()).get("top") or []
    if int(i) >= len(data):
        await c.answer("Natija eskirgan. Qayta qidiring.", show_alert=True)
        return
    item = data[int(i)]
    text = item["caption"] if kind == "cap" else " ".join(item["tags"])
    for part in split_message(with_signature(text)):
        await c.message.answer(f"<code>{esc(part)}</code>")
    await c.answer("Matn yuborildi — bosib nusxalang")


@router.callback_query(F.data.regexp(r"^save:top:\d+$"))
async def save_top(c: CallbackQuery, state: FSMContext):
    i = int(c.data.split(":")[2])
    ids = (await state.get_data()).get("top_ids") or []
    if i >= len(ids):
        await c.answer("Natija eskirgan.", show_alert=True)
        return
    await repo.save_item(c.from_user.id, ids[i], "top3")
    await c.answer("💾 Saqlandi (History da ham bor)")
