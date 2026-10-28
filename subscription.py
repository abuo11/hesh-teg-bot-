from aiogram import F, Router
from aiogram.types import CallbackQuery

from bot.keyboards.reply import main_menu
from bot.services.subscription_service import SubscriptionError, is_subscribed

router = Router()


@router.callback_query(F.data == "sub:check")
async def check(c: CallbackQuery):
    try:
        ok = await is_subscribed(c.bot, c.from_user.id, use_cache=False)
    except SubscriptionError:
        await c.answer("Tekshirib bo‘lmadi. Bot kanalda admin ekanini tekshiring.", show_alert=True)
        return
    if ok:
        await c.message.answer("✅ Obuna tasdiqlandi! Botdan foydalanishingiz mumkin.", reply_markup=main_menu())
        await c.answer()
    else:
        await c.answer("Hali obuna bo‘lmagansiz.", show_alert=True)
