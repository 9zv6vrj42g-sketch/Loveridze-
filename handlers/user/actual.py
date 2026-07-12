from aiogram import F, Router
from aiogram.types import CallbackQuery

from database.requests import get_actual_info
from keyboards.menu import back_kb
from utils.screens import render_screen

router = Router(name="actual")


@router.callback_query(F.data == "menu:actual")
async def show_actual(callback: CallbackQuery) -> None:
    text = await get_actual_info()
    await render_screen(callback.bot, callback.message.chat.id, f"🔥 Актуальное\n\n{text}", back_kb())
    await callback.answer()
