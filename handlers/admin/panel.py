import datetime as dt

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from config import settings
from database.requests import (
    count_images,
    get_active_raffle,
    get_user,
    set_ban,
    set_mute,
)
from handlers.admin.images import _render_delete_list
from handlers.admin.raffle_admin import _preview_text
from handlers.admin.stats import build_stats_text
from keyboards.admin_panel import (
    admin_panel_kb,
    back_to_panel_kb,
    media_submenu_kb,
    raffle_submenu_kb,
    users_submenu_kb,
)
from keyboards.raffle import raffle_admin_preview_kb
from utils.admin_helpers import resolve_target
from utils.states import (
    ActualEditStates,
    AdminPanelStates,
    ImageLibraryStates,
    ModerationCommentStates,
    NotSendStates,
    RaffleCreateStates,
)

router = Router(name="admin_panel")


def _admin_only(event) -> bool:
    return event.from_user.id in settings.admin_ids


PANEL_TITLE = "🛠 Админ-панель\n\nВыбери, что нужно сделать:"


@router.message(Command("admin"))
async def cmd_admin(message: Message, state: FSMContext) -> None:
    if not _admin_only(message):
        return
    await state.clear()
    await message.answer(PANEL_TITLE, reply_markup=admin_panel_kb())


@router.callback_query(F.data == "adminpanel:main")
async def panel_main(callback: CallbackQuery, state: FSMContext) -> None:
    if not _admin_only(callback):
        await callback.answer("Только для администрации", show_alert=True)
        return
    await state.clear()
    await callback.message.edit_text(PANEL_TITLE, reply_markup=admin_panel_kb())
    await callback.answer()


@router.callback_query(F.data == "adminpanel:close")
async def panel_close(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.delete()
    await callback.answer()


@router.callback_query(F.data == "adminpanel:stats")
async def panel_stats(callback: CallbackQuery) -> None:
    if not _admin_only(callback):
        await callback.answer("Только для администрации", show_alert=True)
        return
    text = await build_stats_text(callback.bot)
    await callback.message.edit_text(text, reply_markup=back_to_panel_kb())
    await callback.answer()


@router.callback_query(F.data == "adminpanel:users")
async def panel_users(callback: CallbackQuery) -> None:
    if not _admin_only(callback):
        await callback.answer("Только для администрации", show_alert=True)
        return
    await callback.message.edit_text("👤 Пользователи\n\nВыбери действие:", reply_markup=users_submenu_kb())
    await callback.answer()


@router.callback_query(F.data == "adminpanel:raffle")
async def panel_raffle(callback: CallbackQuery) -> None:
    if not _admin_only(callback):
        await callback.answer("Только для администрации", show_alert=True)
        return
    await callback.message.edit_text("🎉 Розыгрыш\n\nВыбери действие:", reply_markup=raffle_submenu_kb())
    await callback.answer()


@router.callback_query(F.data == "adminpanel:media")
async def panel_media(callback: CallbackQuery) -> None:
    if not _admin_only(callback):
        await callback.answer("Только для администрации", show_alert=True)
        return
    await callback.message.edit_text("🖼 Медиа\n\nВыбери действие:", reply_markup=media_submenu_kb())
    await callback.answer()


# ------------------------------------------------------------------ ✉️ write --
@router.callback_query(F.data == "adminpanel:write")
async def panel_write_start(callback: CallbackQuery, state: FSMContext) -> None:
    if not _admin_only(callback):
        await callback.answer("Только для администрации", show_alert=True)
        return
    await state.set_state(AdminPanelStates.write_target)
    await callback.message.edit_text(
        "✉️ Написать пользователю\n\nПришли id или @username получателя:",
        reply_markup=back_to_panel_kb("adminpanel:users"),
    )
    await callback.answer()


@router.message(AdminPanelStates.write_target, F.text)
async def panel_write_target(message: Message, state: FSMContext) -> None:
    target_id = await resolve_target(message.text.strip())
    if target_id is None:
        await message.answer("Пользователь не найден. Пришли id или @username еще раз:")
        return
    await state.update_data(target_id=target_id)
    await state.set_state(AdminPanelStates.write_text)
    await message.answer("Теперь пришли текст сообщения:")


@router.message(AdminPanelStates.write_text, F.text)
async def panel_write_text(message: Message, state: FSMContext, bot) -> None:
    data = await state.get_data()
    target_id = data.get("target_id")
    await state.clear()
    try:
        await bot.send_message(target_id, message.text)
        await message.answer("✅ Отправлено.", reply_markup=admin_panel_kb())
    except Exception as exc:  # noqa: BLE001
        await message.answer(f"⚠️ Не удалось отправить: {exc}", reply_markup=admin_panel_kb())


# -------------------------------------------------------------------- 🚫 ban --
@router.callback_query(F.data == "adminpanel:ban")
async def panel_ban_start(callback: CallbackQuery, state: FSMContext) -> None:
    if not _admin_only(callback):
        await callback.answer("Только для администрации", show_alert=True)
        return
    await state.set_state(AdminPanelStates.ban_target)
    await callback.message.edit_text(
        "🚫 Бан\n\nПришли id или @username пользователя:",
        reply_markup=back_to_panel_kb("adminpanel:users"),
    )
    await callback.answer()


@router.message(AdminPanelStates.ban_target, F.text)
async def panel_ban_target(message: Message, state: FSMContext) -> None:
    target_id = await resolve_target(message.text.strip())
    if target_id is None:
        await message.answer("Пользователь не найден. Пришли id или @username еще раз:")
        return
    await set_ban(target_id, True)
    await state.update_data(comment_action="ban", comment_target=target_id)
    await state.set_state(ModerationCommentStates.waiting_comment)
    await message.answer("Пользователь забанен ✅\nНапиши комментарий с причиной (или «-» чтобы пропустить).")


# ----------------------------------------------------------------- ♻️ unban --
@router.callback_query(F.data == "adminpanel:unban")
async def panel_unban_start(callback: CallbackQuery, state: FSMContext) -> None:
    if not _admin_only(callback):
        await callback.answer("Только для администрации", show_alert=True)
        return
    await state.set_state(AdminPanelStates.unban_target)
    await callback.message.edit_text(
        "♻️ Разбан\n\nПришли id или @username пользователя:",
        reply_markup=back_to_panel_kb("adminpanel:users"),
    )
    await callback.answer()


@router.message(AdminPanelStates.unban_target, F.text)
async def panel_unban_target(message: Message, state: FSMContext) -> None:
    target_id = await resolve_target(message.text.strip())
    if target_id is None:
        await message.answer("Пользователь не найден. Пришли id или @username еще раз:")
        return
    await set_ban(target_id, False, comment=None)
    await state.clear()
    await message.answer("Пользователь разбанен ✅", reply_markup=admin_panel_kb())


# --------------------------------------------------------------- ℹ️ baninfo --
@router.callback_query(F.data == "adminpanel:baninfo")
async def panel_baninfo_start(callback: CallbackQuery, state: FSMContext) -> None:
    if not _admin_only(callback):
        await callback.answer("Только для администрации", show_alert=True)
        return
    await state.set_state(AdminPanelStates.baninfo_target)
    await callback.message.edit_text(
        "ℹ️ Инфо о бане\n\nПришли id или @username пользователя:",
        reply_markup=back_to_panel_kb("adminpanel:users"),
    )
    await callback.answer()


@router.message(AdminPanelStates.baninfo_target, F.text)
async def panel_baninfo_target(message: Message, state: FSMContext) -> None:
    target_id = await resolve_target(message.text.strip())
    if target_id is None:
        await message.answer("Пользователь не найден. Пришли id или @username еще раз:")
        return
    await state.clear()
    user = await get_user(target_id)
    if not user or not user.is_banned:
        await message.answer("Пользователь не забанен.", reply_markup=admin_panel_kb())
        return
    await message.answer(f"🚫 Забанен.\nКомментарий: {user.ban_comment or '—'}", reply_markup=admin_panel_kb())


# -------------------------------------------------------------------- 🔇 mute --
@router.callback_query(F.data == "adminpanel:mute")
async def panel_mute_start(callback: CallbackQuery, state: FSMContext) -> None:
    if not _admin_only(callback):
        await callback.answer("Только для администрации", show_alert=True)
        return
    await state.set_state(AdminPanelStates.mute_target)
    await callback.message.edit_text(
        "🔇 Мьют\n\nПришли id или @username пользователя:",
        reply_markup=back_to_panel_kb("adminpanel:users"),
    )
    await callback.answer()


@router.message(AdminPanelStates.mute_target, F.text)
async def panel_mute_target(message: Message, state: FSMContext) -> None:
    target_id = await resolve_target(message.text.strip())
    if target_id is None:
        await message.answer("Пользователь не найден. Пришли id или @username еще раз:")
        return
    await state.update_data(target_id=target_id)
    await state.set_state(AdminPanelStates.mute_minutes)
    await message.answer("На сколько минут замьютить? Пришли число (или «-» для 60 минут по умолчанию):")


@router.message(AdminPanelStates.mute_minutes, F.text)
async def panel_mute_minutes(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    target_id = data.get("target_id")
    raw = message.text.strip()
    minutes = int(raw) if raw.isdigit() else 60
    until = dt.datetime.utcnow() + dt.timedelta(minutes=minutes)
    await set_mute(target_id, until)
    await state.update_data(comment_action="mute", comment_target=target_id)
    await state.set_state(ModerationCommentStates.waiting_comment)
    await message.answer(
        f"Пользователь замьючен на {minutes} мин ✅\nНапиши комментарий с причиной (или «-» чтобы пропустить)."
    )


# ------------------------------------------------------------------ 🔊 unmute --
@router.callback_query(F.data == "adminpanel:unmute")
async def panel_unmute_start(callback: CallbackQuery, state: FSMContext) -> None:
    if not _admin_only(callback):
        await callback.answer("Только для администрации", show_alert=True)
        return
    await state.set_state(AdminPanelStates.unmute_target)
    await callback.message.edit_text(
        "🔊 Размьют\n\nПришли id или @username пользователя:",
        reply_markup=back_to_panel_kb("adminpanel:users"),
    )
    await callback.answer()


@router.message(AdminPanelStates.unmute_target, F.text)
async def panel_unmute_target(message: Message, state: FSMContext) -> None:
    target_id = await resolve_target(message.text.strip())
    if target_id is None:
        await message.answer("Пользователь не найден. Пришли id или @username еще раз:")
        return
    await set_mute(target_id, None, comment=None)
    await state.clear()
    await message.answer("Мьют снят ✅", reply_markup=admin_panel_kb())


# ---------------------------------------------------------------- 🎉 raffle --
@router.callback_query(F.data == "adminpanel:givestart")
async def panel_givestart(callback: CallbackQuery, state: FSMContext) -> None:
    if not _admin_only(callback):
        await callback.answer("Только для администрации", show_alert=True)
        return
    await state.set_state(RaffleCreateStates.number)
    await callback.message.edit_text(
        "🆕 Создание розыгрыша\n\nШаг 1/5. Укажи номер розыгрыша (число):",
        reply_markup=back_to_panel_kb("adminpanel:raffle"),
    )
    await callback.answer()


@router.callback_query(F.data == "adminpanel:giveinfo")
async def panel_giveinfo(callback: CallbackQuery, state: FSMContext) -> None:
    if not _admin_only(callback):
        await callback.answer("Только для администрации", show_alert=True)
        return
    raffle = await get_active_raffle()
    if raffle is None:
        await callback.message.edit_text(
            "Нет активного розыгрыша. Создай его через «🆕 Создать розыгрыш».",
            reply_markup=raffle_submenu_kb(),
        )
        await callback.answer()
        return
    await state.update_data(raffle_id=raffle.id)
    text = await _preview_text(raffle)
    await callback.message.edit_text(text, reply_markup=raffle_admin_preview_kb())
    await callback.answer()


# ------------------------------------------------------------------ ❗️ actual --
@router.callback_query(F.data == "adminpanel:actual")
async def panel_actual(callback: CallbackQuery, state: FSMContext) -> None:
    if not _admin_only(callback):
        await callback.answer("Только для администрации", show_alert=True)
        return
    await state.set_state(ActualEditStates.waiting_text)
    await callback.message.edit_text(
        "❗️ Отправь новый текст для раздела «Актуальное»:",
        reply_markup=back_to_panel_kb(),
    )
    await callback.answer()


# --------------------------------------------------------------- 📢 broadcast --
@router.callback_query(F.data == "adminpanel:broadcast")
async def panel_broadcast(callback: CallbackQuery, state: FSMContext) -> None:
    if not _admin_only(callback):
        await callback.answer("Только для администрации", show_alert=True)
        return
    await state.set_state(NotSendStates.waiting_content)
    await callback.message.edit_text(
        "📢 Пришли текст, фото, видео или ссылку для рассылки всем, у кого включены уведомления:",
        reply_markup=back_to_panel_kb(),
    )
    await callback.answer()


# -------------------------------------------------------------------- 🖼 media --
@router.callback_query(F.data == "adminpanel:addimage")
async def panel_addimage(callback: CallbackQuery, state: FSMContext) -> None:
    if not _admin_only(callback):
        await callback.answer("Только для администрации", show_alert=True)
        return
    await state.set_state(ImageLibraryStates.collecting)
    await state.update_data(media_type="photo")
    current = await count_images("photo")
    await callback.message.edit_text(
        "📸 Пришли одно или несколько квадратных фото подряд.\n"
        f"Сейчас фото в библиотеке: {current}.\n\nКогда закончишь — отправь /done.",
        reply_markup=back_to_panel_kb("adminpanel:media"),
    )
    await callback.answer()


@router.callback_query(F.data == "adminpanel:addsticker")
async def panel_addsticker(callback: CallbackQuery, state: FSMContext) -> None:
    if not _admin_only(callback):
        await callback.answer("Только для администрации", show_alert=True)
        return
    await state.set_state(ImageLibraryStates.collecting)
    await state.update_data(media_type="sticker")
    current = await count_images("sticker")
    await callback.message.edit_text(
        "🎭 Пришли один или несколько стикеров подряд.\n"
        f"Сейчас стикеров в библиотеке: {current}.\n\nКогда закончишь — отправь /done.",
        reply_markup=back_to_panel_kb("adminpanel:media"),
    )
    await callback.answer()


@router.callback_query(F.data == "adminpanel:imagescount")
async def panel_imagescount(callback: CallbackQuery) -> None:
    if not _admin_only(callback):
        await callback.answer("Только для администрации", show_alert=True)
        return
    photos = await count_images("photo")
    stickers = await count_images("sticker")
    await callback.message.edit_text(
        f"📸 Фото в библиотеке: {photos}\n🎭 Стикеров в библиотеке: {stickers}",
        reply_markup=back_to_panel_kb("adminpanel:media"),
    )
    await callback.answer()


@router.callback_query(F.data == "adminpanel:imagedelete")
async def panel_imagedelete(callback: CallbackQuery) -> None:
    if not _admin_only(callback):
        await callback.answer("Только для администрации", show_alert=True)
        return
    text, kb = await _render_delete_list(0)
    if kb is None:
        kb = back_to_panel_kb("adminpanel:media")
    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()
