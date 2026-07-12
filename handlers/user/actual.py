from aiogram import F, Router
from aiogram.types import CallbackQuery

from database.requests import get_actual_info
from keyboards.menu import back_kb

router = Router(name="actual")


@router.callback_query(F.data == "menu:actual")
async def show_actual(callback: CallbackQuery) -> None:
    text = await get_actual_info()
    await callback.message.edit_text(f"💥 Актуальное\n\n{text}", reply_markup=back_kb())
    await callback.answer()
