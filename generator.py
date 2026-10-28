from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from bot.keyboards import inline as K
from bot.loader import repo
from bot.services.directions import get_direction
from bot.services.hashtag_generator import generate
from bot.utils.text_formatter import build_copy_text, esc, split_message

router = Router()


class Gen(StatesGroup):
    topic = State()


@router.callback_query(F.data.regexp(r"^gen:\d+$"))
async def start_gen(c: CallbackQuery, state: FSMContext):
    idx = int(c.data.split(":")[1])
    await state.set_state(Gen.topic)
    await state.update_data(gen_idx=idx, g_topic="", g_lang="uz", g_style="fun", g_count=15)
    await c.message.answer(
        "✍️ Video mavzusini yozing (masalan: <i>Barcelona yangi transferi</i>).\n"
        "Xohlamasangiz, o‘tkazib yuboring.", reply_markup=K.skip_kb("gtopic:skip"))
    await c.answer()


@router.message(Gen.topic, F.text)
async def got_topic(m: Message, state: FSMContext):
    await state.update_data(g_topic=m.text.strip()[:200])
    await state.set_state(None)
    await m.answer("🌐 Kontent tilini tanlang:", reply_markup=K.lang_kb())


@router.callback_query(F.data == "gtopic:skip")
async def skip_topic(c: CallbackQuery, state: FSMContext):
    await state.set_state(None)
    await c.message.answer("🌐 Kontent tilini tanlang:", reply_markup=K.lang_kb())
    await c.answer()


@router.callback_query(F.data.startswith("glang:"))
async def set_lang(c: CallbackQuery, state: FSMContext):
    await state.update_data(g_lang=c.data.split(":")[1])
    await c.message.answer("🎭 Caption uslubini tanlang:", reply_markup=K.style_kb())
    await c.answer()


@router.callback_query(F.data.startswith("gstyle:"))
async def set_style(c: CallbackQuery, state: FSMContext):
    await state.update_data(g_style=c.data.split(":")[1])
    await c.message.answer("🔢 Nechta hashtag kerak?", reply_markup=K.count_kb())
    await c.answer()


@router.callback_query(F.data.startswith("gcount:"))
async def set_count(c: CallbackQuery, state: FSMContext):
    await state.update_data(g_count=int(c.data.split(":")[1]))
    await c.answer()
    await run_generation(c, state)


@router.callback_query(F.data == "gen:again")
async def again(c: CallbackQuery, state: FSMContext):
    await c.answer()
    if "gen_idx" not in await state.get_data():
        await c.message.answer("Avval yo‘nalishni tanlang.", reply_markup=K.directions_kb("menu"))
        return
    await run_generation(c, state)


async def run_generation(c: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    d = get_direction(data["gen_idx"])
    wait = await c.message.answer("⏳ Tahlil qilinmoqda...")
    await repo.bump("generator")
    res = await generate(d, data.get("g_topic", ""), data.get("g_lang", "uz"),
                         data.get("g_style", "fun"), data.get("g_count", 15))
    await repo.log_api(f"generator_{res.engine}", True)
    hid = await repo.add_history(c.from_user.id, "ai_generated", res.caption, res.hashtags,
                                 source=f"AI ({res.engine})", direction=d.name)
    full = build_copy_text(res.caption, res.hashtags)
    await state.update_data(gen_full=full, gen_tags=" ".join(res.hashtags), gen_hid=hid)
    await wait.edit_text(
        f"{d.emoji} <b>{esc(d.name)}</b>\n\n{esc(res.caption)}\n\n{esc(' '.join(res.hashtags))}\n\n"
        f"<i>🤖 {esc(res.note)}</i>\n\n\n{esc(full.rsplit(chr(10), 1)[-1])}",
        reply_markup=K.gen_result_kb())


@router.callback_query(F.data.regexp(r"^cp:gen:(full|tags)$"))
async def copy_gen(c: CallbackQuery, state: FSMContext):
    kind = c.data.split(":")[2]
    data = await state.get_data()
    text = data.get("gen_full") if kind == "full" else data.get("gen_tags")
    if not text:
        await c.answer("Natija topilmadi. Qayta yarating.", show_alert=True)
        return
    if kind == "tags":
        from bot.utils.text_formatter import with_signature
        text = with_signature(text)
    for part in split_message(text):
        await c.message.answer(f"<code>{esc(part)}</code>")
    await c.answer("Matn yuborildi — bosib nusxalang")


@router.callback_query(F.data == "save:gen")
async def save_gen(c: CallbackQuery, state: FSMContext):
    hid = (await state.get_data()).get("gen_hid")
    if not hid:
        await c.answer("Saqlanadigan natija yo‘q.", show_alert=True)
        return
    await repo.save_item(c.from_user.id, hid, "ai_generated")
    await c.answer("💾 Saqlandi (History da ham bor)")
