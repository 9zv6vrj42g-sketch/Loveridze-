from aiogram import F, Router
from aiogram.types import CallbackQuery

from database.requests import get_or_create_user, set_notifications
from keyboards.notifications import notifications_kb
from utils.texts import NOTIFICATIONS_OFF, NOTIFICATIONS_ON, NOTIFICATIONS_TEXT

router = Router(name="notifications")


@router.callback_query(F.data == "menu:notifications")
async def show_notifications(callback: CallbackQuery) -> None:
    user = await get_or_create_user(
        callback.from_user.id, callback.from_user.username, callback.from_user.full_name
    )
    await callback.message.edit_text(NOTIFICATIONS_TEXT, reply_markup=notifications_kb(user.notifications_on))
    await callback.answer()


@router.callback_query(F.data == "notif:on")
async def notif_on(callback: CallbackQuery) -> None:
    await set_notifications(callback.from_user.id, True)
    await callback.message.edit_text(
        f"{NOTIFICATIONS_TEXT}\n\n{NOTIFICATIONS_ON}", reply_markup=notifications_kb(True)
    )
    await callback.answer("Уведомления включены")


@router.callback_query(F.data == "notif:off")
async def notif_off(callback: CallbackQuery) -> None:
    await set_notifications(callback.from_user.id, False)
    await callback.message.edit_text(
        f"{NOTIFICATIONS_TEXT}\n\n{NOTIFICATIONS_OFF}", reply_markup=notifications_kb(False)
    )
    await callback.answer("Уведомления отключены")
