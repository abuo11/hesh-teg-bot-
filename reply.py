from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

BTN_TOP = "🔥 TOP hashtaglar"
BTN_GEN = "🤖 AI hashtag yaratish"
BTN_VIDEO = "🎬 Video analiz"
BTN_CAB = "📱 Kabinet"
BTN_HELP = "ℹ️ Yordam"


def main_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BTN_TOP), KeyboardButton(text=BTN_GEN)],
            [KeyboardButton(text=BTN_VIDEO), KeyboardButton(text=BTN_CAB)],
            [KeyboardButton(text=BTN_HELP)],
        ],
        resize_keyboard=True,
    )
