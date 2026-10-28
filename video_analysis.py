from __future__ import annotations

import asyncio
import tempfile
from pathlib import Path

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from bot.config import settings
from bot.keyboards.inline import directions_kb, video_result_kb
from bot.keyboards.reply import BTN_VIDEO
from bot.loader import repo
from bot.services.directions import get_direction
from bot.services.video_analyzer import analyze_video, render_report
from bot.utils.logger import logger

router = Router()
_sem = asyncio.Semaphore(2)  # bir vaqtda 2 ta analiz — boshqalar bloklanmaydi
ALLOWED_EXT = {".mp4", ".mov", ".mkv", ".webm", ".avi", ".m4v"}


class VideoSt(StatesGroup):
    waiting = State()


@router.message(F.text == BTN_VIDEO)
async def video_menu(m: Message, state: FSMContext):
    await state.clear()
    await m.answer("📂 Video qaysi yo‘nalish uchun?", reply_markup=directions_kb("video"))


@router.callback_query(F.data.regexp(r"^dir:video:\d+$"))
async def pick(c: CallbackQuery, state: FSMContext):
    idx = int(c.data.split(":")[2])
    await state.set_state(VideoSt.waiting)
    await state.update_data(video_idx=idx)
    await c.message.answer("🎬 Videongizni yuboring. Men uning texnik sifatini, dastlabki hook qismini va "
                           "kontentdagi kamchiliklarni tahlil qilaman.")
    await c.answer()


@router.message(VideoSt.waiting, F.video | F.document)
async def got_video(m: Message, state: FSMContext):
    obj = m.video or m.document
    name = getattr(obj, "file_name", None) or "video.mp4"
    ext = Path(name).suffix.lower() or ".mp4"
    if m.document and (not (m.document.mime_type or "").startswith("video/") and ext not in ALLOWED_EXT):
        await m.answer("⚠️ Faqat video fayl yuboring (mp4, mov, mkv, webm).")
        return
    if ext not in ALLOWED_EXT:
        ext = ".mp4"
    if obj.file_size and obj.file_size > settings.max_video_mb * 1048576:
        await m.answer(f"⚠️ Video hajmi {settings.max_video_mb} MB dan oshmasligi kerak "
                       f"(Telegram bot API cheklovi). Siqib qayta yuboring.")
        return

    idx = (await state.get_data()).get("video_idx", 0)
    d = get_direction(idx)
    wait = await m.answer("⏳ Tahlil qilinmoqda...")
    await repo.bump("video")
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / f"v{m.message_id}{ext}"
        try:
            await m.bot.download(obj, destination=path)
            await wait.edit_text("⏳ Kadrlar tahlil qilinmoqda...")
            async with _sem:
                rep = await asyncio.to_thread(analyze_video, path, d.name)
        except ValueError as e:
            await wait.edit_text(f"⚠️ {e}", reply_markup=video_result_kb(idx))
            return
        except Exception:
            logger.exception("video analiz xatosi")
            await repo.log_api("video_analyzer", False, "exception")
            await wait.edit_text("⚠️ Tahlil vaqtida xatolik. Qayta urinib ko‘ring.",
                                 reply_markup=video_result_kb(idx))
            return
    text = render_report(rep, f"{d.emoji} {d.name}")
    await repo.add_video_analysis(m.from_user.id, d.name, rep.score, text)
    await repo.log_api("video_analyzer", True)
    await state.set_state(None)
    await wait.edit_text(text, reply_markup=video_result_kb(idx))


@router.message(VideoSt.waiting)
async def not_video(m: Message):
    await m.answer("🎬 Iltimos, video yuboring.")
