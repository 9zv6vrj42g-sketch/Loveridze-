from aiogram import F, Router
from aiogram.types import CallbackQuery

from keyboards.content import content_kb
from utils.texts import CONTENT_TEXT

router = Router(name="content")


@router.callback_query(F.data == "menu:content")
async def show_content(callback: CallbackQuery) -> None:
    await callback.message.edit_text(CONTENT_TEXT, reply_markup=content_kb())
    await callback.answer()
