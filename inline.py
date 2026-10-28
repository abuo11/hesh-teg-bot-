from aiogram.types import InlineKeyboardButton as B, InlineKeyboardMarkup as M
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.config import settings
from bot.services.directions import DIRECTIONS

BACK = B(text="⬅️ Orqaga", callback_data="back:main")


def subscription_kb() -> M:
    return M(inline_keyboard=[
        [B(text="📢 Kanalga obuna bo‘lish", url=settings.required_channel_url)],
        [B(text="✅ Obunani tekshirish", callback_data="sub:check")],
    ])


def directions_kb(mode: str) -> M:
    """mode: menu | video. Ikki ustunli 16 ta yo'nalish."""
    b = InlineKeyboardBuilder()
    for i, d in enumerate(DIRECTIONS):
        b.button(text=f"{d.emoji} {d.name}", callback_data=f"dir:{mode}:{i}")
    b.adjust(2)
    b.row(BACK)
    return b.as_markup()


def direction_actions_kb(idx: int) -> M:
    return M(inline_keyboard=[
        [B(text="🔥 Oxirgi 7 kunlik TOP videolar", callback_data=f"top:{idx}")],
        [B(text="🤖 Men uchun maxsus hashtag yarat", callback_data=f"gen:{idx}")],
        [B(text="⬅️ Orqaga", callback_data="back:dirs")],
    ])


def skip_kb(cb: str, back: str = "back:main") -> M:
    return M(inline_keyboard=[[B(text="⏭ O‘tkazib yuborish", callback_data=cb)],
                              [B(text="⬅️ Orqaga", callback_data=back)]])


def lang_kb() -> M:
    return M(inline_keyboard=[
        [B(text="🇺🇿 O‘zbek", callback_data="glang:uz"), B(text="🇷🇺 Rus", callback_data="glang:ru"),
         B(text="🇬🇧 Ingliz", callback_data="glang:en")],
        [B(text="⏭ O‘tkazib yuborish", callback_data="glang:uz")],
        [B(text="⬅️ Orqaga", callback_data="back:main")],
    ])


def style_kb() -> M:
    return M(inline_keyboard=[
        [B(text="😄 Qiziqarli", callback_data="gstyle:fun"), B(text="🎯 Jiddiy", callback_data="gstyle:serious")],
        [B(text="🔥 Motivatsion", callback_data="gstyle:motiv"), B(text="✂️ Qisqa", callback_data="gstyle:short")],
        [B(text="⏭ O‘tkazib yuborish", callback_data="gstyle:fun")],
        [B(text="⬅️ Orqaga", callback_data="back:main")],
    ])


def count_kb() -> M:
    return M(inline_keyboard=[
        [B(text=str(n), callback_data=f"gcount:{n}") for n in (10, 15, 20, 30)],
        [B(text="⏭ O‘tkazib yuborish", callback_data="gcount:15")],
        [B(text="⬅️ Orqaga", callback_data="back:main")],
    ])


def gen_result_kb() -> M:
    return M(inline_keyboard=[
        [B(text="📋 To‘liq matnni nusxalash", callback_data="cp:gen:full")],
        [B(text="# Faqat hashtaglarni nusxalash", callback_data="cp:gen:tags")],
        [B(text="🔄 Yangi variant", callback_data="gen:again"), B(text="💾 Saqlash", callback_data="save:gen")],
        [B(text="⬅️ Orqaga", callback_data="back:main")],
    ])


def top_item_kb(i: int, url: str) -> M:
    return M(inline_keyboard=[
        [B(text="📋 Captionni nusxalash", callback_data=f"cp:top:cap:{i}"),
         B(text="# Hashtaglarni nusxalash", callback_data=f"cp:top:tags:{i}")],
        [B(text="▶️ Videoni ochish", url=url), B(text="💾 Saqlash", callback_data=f"save:top:{i}")],
    ])


def after_top_kb() -> M:
    return M(inline_keyboard=[[BACK]])


def video_result_kb(idx: int) -> M:
    return M(inline_keyboard=[
        [B(text="🔁 Qayta analiz qilish", callback_data=f"dir:video:{idx}"),
         B(text="# Hashtag yaratish", callback_data=f"gen:{idx}")],
        [B(text="⬅️ Orqaga", callback_data="back:main")],
    ])


def admin_kb() -> M:
    return M(inline_keyboard=[[B(text="🔄 Yangilash", callback_data="admin:refresh")]])
