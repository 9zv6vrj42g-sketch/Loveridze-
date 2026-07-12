from aiogram import F, Router
from aiogram.types import CallbackQuery

from config import settings

router = Router(name="moderation")


@router.callback_query(F.data.startswith("mod:approve:"))
async def mod_approve(callback: CallbackQuery) -> None:
    if callback.from_user.id not in settings.admin_ids:
        await callback.answer("Только для администрации", show_alert=True)
        return
    suggestion_id = callback.data.split(":")[-1]
    await callback.message.edit_caption(
        caption=(callback.message.caption or "") + "\n\n✅ Одобрено"
    ) if callback.message.caption else await callback.message.edit_text(
        (callback.message.text or "") + "\n\n✅ Одобрено"
    )
    await callback.answer(f"Предложение #{suggestion_id} одобрено")


@router.callback_query(F.data.startswith("mod:reject:"))
async def mod_reject(callback: CallbackQuery) -> None:
    if callback.from_user.id not in settings.admin_ids:
        await callback.answer("Только для администрации", show_alert=True)
        return
    suggestion_id = callback.data.split(":")[-1]
    await callback.message.edit_caption(
        caption=(callback.message.caption or "") + "\n\n❌ Отклонено"
    ) if callback.message.caption else await callback.message.edit_text(
        (callback.message.text or "") + "\n\n❌ Отклонено"
    )
    await callback.answer(f"Предложение #{suggestion_id} отклонено")
