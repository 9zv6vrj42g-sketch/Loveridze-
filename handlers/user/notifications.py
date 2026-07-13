from aiogram import F, Router
from aiogram.types import CallbackQuery

from database.requests import get_or_create_user, set_notifications
from keyboards.notifications import notifications_kb
from utils.screens import render_screen
from utils.texts import NOTIFICATIONS_OFF, NOTIFICATIONS_ON, NOTIFICATIONS_TEXT

router = Router(name="notifications")


@router.callback_query(F.data == "raffle:notifications")
async def show_notifications(callback: CallbackQuery) -> None:
    user = await get_or_create_user(
        callback.from_user.id, callback.from_user.username, callback.from_user.full_name
    )
    await render_screen(
        callback.bot, callback.message.chat.id, NOTIFICATIONS_TEXT, notifications_kb(user.notifications_on)
    )
    await callback.answer()


@router.callback_query(F.data == "notif:on")
async def notif_on(callback: CallbackQuery) -> None:
    await set_notifications(callback.from_user.id, True)
    await render_screen(
        callback.bot,
        callback.message.chat.id,
        f"{NOTIFICATIONS_TEXT}\n\n{NOTIFICATIONS_ON}",
        notifications_kb(True),
    )
    await callback.answer("Уведомления включены")


@router.callback_query(F.data == "notif:off")
async def notif_off(callback: CallbackQuery) -> None:
    await set_notifications(callback.from_user.id, False)
    await render_screen(
        callback.bot,
        callback.message.chat.id,
        f"{NOTIFICATIONS_TEXT}\n\n{NOTIFICATIONS_OFF}",
        notifications_kb(False),
    )
    await callback.answer("Уведомления отключены")
