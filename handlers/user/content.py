from aiogram import F, Router
from aiogram.types import CallbackQuery

from keyboards.content import content_kb
from utils.screens import render_screen
from utils.texts import CONTENT_TEXT

router = Router(name="content")


@router.callback_query(F.data == "menu:content")
async def show_content(callback: CallbackQuery) -> None:
    await render_screen(callback.bot, callback.message.chat.id, CONTENT_TEXT, content_kb())
    await callback.answer()
