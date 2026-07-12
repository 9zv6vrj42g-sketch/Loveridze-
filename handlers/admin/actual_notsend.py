import asyncio

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from config import settings
from database.requests import log_broadcast, notified_user_ids, set_actual_info
from utils.states import ActualEditStates, NotSendStates
from utils.texts import NOTSEND_FOOTER

router = Router(name="admin_actual_notsend")


def _admin_only(message: Message) -> bool:
    return message.from_user.id in settings.admin_ids


# ------------------------------------------------------------- /editactual --
@router.message(Command("editactual"))
async def cmd_editactual(message: Message, state: FSMContext) -> None:
    if not _admin_only(message):
        return
    await state.set_state(ActualEditStates.waiting_text)
    await message.answer("Отправь новый текст для раздела 💥 Актуальное:")


@router.message(ActualEditStates.waiting_text, F.text)
async def editactual_receive(message: Message, state: FSMContext) -> None:
    await set_actual_info(message.text)
    await state.clear()
    await message.answer("✅ Раздел «Актуальное» обновлен.")


# ------------------------------------------------------------------ /notsend --
@router.message(Command("notsend"))
async def cmd_notsend(message: Message, state: FSMContext) -> None:
    if not _admin_only(message):
        return
    await state.set_state(NotSendStates.waiting_content)
    await message.answer("Отправь текст, фото, видео или ссылку для рассылки:")


@router.message(NotSendStates.waiting_content)
async def notsend_broadcast(message: Message, state: FSMContext, bot) -> None:
    await state.clear()
    recipients = await notified_user_ids()
    sent = 0

    async def _send_one(user_id: int) -> bool:
        try:
            if message.photo:
                await bot.send_photo(
                    user_id, message.photo[-1].file_id, caption=(message.caption or "") + NOTSEND_FOOTER
                )
            elif message.video:
                await bot.send_video(
                    user_id, message.video.file_id, caption=(message.caption or "") + NOTSEND_FOOTER
                )
            elif message.document:
                await bot.send_document(
                    user_id, message.document.file_id, caption=(message.caption or "") + NOTSEND_FOOTER
                )
            else:
                await bot.send_message(user_id, (message.text or "") + NOTSEND_FOOTER)
            return True
        except Exception:  # noqa: BLE001
            return False

    for user_id in recipients:
        ok = await _send_one(user_id)
        sent += int(ok)
        await asyncio.sleep(0.05)  # stay well under Telegram's rate limits

    await log_broadcast(sent)
    await message.answer(f"✅ Рассылка завершена. Доставлено: {sent}/{len(recipients)}")
