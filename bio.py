from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from bot.keyboards.webapp import cabinet_kb

router = Router()


@router.message(Command("bio"))
async def bio_cmd(m: Message):
    await m.answer("👤 Instagram bio olish kabinetdagi <b>Bio yuklash</b> bo‘limida ishlaydi.",
                   reply_markup=cabinet_kb())
