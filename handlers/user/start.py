import random

from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.types import CallbackQuery, Message

from database.requests import get_or_create_user
from keyboards.menu import main_menu_kb
from utils.texts import GREETINGS, MAIN_MENU_TEXT

router = Router(name="start")


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    await get_or_create_user(
        message.from_user.id, message.from_user.username, message.from_user.full_name
    )
    greeting = random.choice(GREETINGS)
    await message.answer(f"{greeting}\n\n{MAIN_MENU_TEXT}", reply_markup=main_menu_kb())


@router.callback_query(F.data == "menu:main")
async def back_to_main(callback: CallbackQuery) -> None:
    await callback.message.edit_text(MAIN_MENU_TEXT, reply_markup=main_menu_kb())
    await callback.answer()
