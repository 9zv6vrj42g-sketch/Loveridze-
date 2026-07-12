import datetime as dt

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from config import settings
from database.requests import create_suggestion, get_or_create_user, set_suggestion_mod_message, touch_suggestion_cooldown
from keyboards.menu import back_kb
from keyboards.suggest import (
    mod_queue_kb,
    suggest_description_kb,
    suggest_media_kb,
    suggest_mode_kb,
    suggest_preview_kb,
)
from utils.states import SuggestStates
from utils.texts import (
    SUGGEST_COOLDOWN_ACTIVE,
    SUGGEST_INTRO,
    SUGGEST_PREVIEW_TITLE,
    SUGGEST_SENT,
    SUGGEST_STEP_DESCRIPTION,
    SUGGEST_STEP_MEDIA,
)

router = Router(name="suggest")


def _cooldown_remaining(last_at: dt.datetime | None) -> int | None:
    if last_at is None:
        return None
    elapsed = dt.datetime.utcnow() - last_at
    remaining = dt.timedelta(minutes=settings.SUGGESTION_COOLDOWN_MINUTES) - elapsed
    if remaining.total_seconds() <= 0:
        return None
    return max(1, int(remaining.total_seconds() // 60))


@router.callback_query(F.data == "menu:suggest")
async def suggest_intro(callback: CallbackQuery, state: FSMContext) -> None:
    user = await get_or_create_user(
        callback.from_user.id, callback.from_user.username, callback.from_user.full_name
    )
    remaining = _cooldown_remaining(user.last_suggestion_at)
    if remaining is not None:
        await callback.message.edit_text(
            SUGGEST_COOLDOWN_ACTIVE.format(minutes=remaining), reply_markup=back_kb()
        )
        await callback.answer()
        return

    await state.clear()
    await callback.message.edit_text(SUGGEST_INTRO, reply_markup=suggest_mode_kb())
    await callback.answer()


@router.callback_query(F.data.startswith("suggest:mode:"))
async def suggest_choose_mode(callback: CallbackQuery, state: FSMContext) -> None:
    mode = callback.data.split(":")[-1]  # anon / public
    await state.update_data(is_anonymous=(mode == "anon"))
    await state.set_state(SuggestStates.waiting_media)
    await callback.message.edit_text(SUGGEST_STEP_MEDIA, reply_markup=suggest_media_kb())
    await callback.answer()


@router.message(SuggestStates.waiting_media, F.photo | F.video | F.document)
async def suggest_receive_media(message: Message, state: FSMContext) -> None:
    if message.photo:
        media_type, file_id = "photo", message.photo[-1].file_id
    elif message.video:
        media_type, file_id = "video", message.video.file_id
    else:
        media_type, file_id = "document", message.document.file_id

    await state.update_data(media_type=media_type, media_file_id=file_id)
    await message.answer("Медиа получено ✅\n\n" + SUGGEST_STEP_MEDIA, reply_markup=suggest_media_kb())


@router.callback_query(SuggestStates.waiting_media, F.data == "suggest:next")
async def suggest_media_next(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    if not data.get("media_file_id"):
        await callback.answer("Сначала прикрепи фото, видео или файл", show_alert=True)
        return
    await state.set_state(SuggestStates.waiting_description)
    await callback.message.answer(SUGGEST_STEP_DESCRIPTION, reply_markup=suggest_description_kb())
    await callback.answer()


@router.callback_query(F.data == "suggest:back_to_media")
async def suggest_back_to_media(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(SuggestStates.waiting_media)
    await callback.message.edit_text(SUGGEST_STEP_MEDIA, reply_markup=suggest_media_kb())
    await callback.answer()


@router.message(SuggestStates.waiting_description, F.text)
async def suggest_receive_description(message: Message, state: FSMContext) -> None:
    await state.update_data(description=message.text)
    await message.answer("Описание получено ✅\n\n" + SUGGEST_STEP_DESCRIPTION, reply_markup=suggest_description_kb())


@router.callback_query(SuggestStates.waiting_description, F.data == "suggest:next")
async def suggest_description_next(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    if not data.get("description"):
        await callback.answer("Сначала отправь описание", show_alert=True)
        return
    await state.set_state(SuggestStates.preview)
    await _send_preview(callback.message, data)
    await callback.answer()


async def _send_preview(message: Message, data: dict) -> None:
    mode = "☑️ Анонимно" if data.get("is_anonymous") else "✅ Публично"
    caption = f"{SUGGEST_PREVIEW_TITLE}\n\n{mode}\n\n{data.get('description', '')}"
    media_type = data.get("media_type")
    file_id = data.get("media_file_id")
    if media_type == "photo":
        await message.answer_photo(file_id, caption=caption, reply_markup=suggest_preview_kb())
    elif media_type == "video":
        await message.answer_video(file_id, caption=caption, reply_markup=suggest_preview_kb())
    elif media_type == "document":
        await message.answer_document(file_id, caption=caption, reply_markup=suggest_preview_kb())
    else:
        await message.answer(caption, reply_markup=suggest_preview_kb())


@router.callback_query(SuggestStates.preview, F.data == "suggest:edit")
async def suggest_edit(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(SuggestStates.waiting_media)
    await callback.message.answer(SUGGEST_STEP_MEDIA, reply_markup=suggest_media_kb())
    await callback.answer()


@router.callback_query(SuggestStates.preview, F.data == "suggest:submit")
async def suggest_submit(callback: CallbackQuery, state: FSMContext, bot) -> None:
    data = await state.get_data()
    user = callback.from_user

    suggestion = await create_suggestion(
        user_id=user.id,
        is_anonymous=bool(data.get("is_anonymous")),
        media_type=data.get("media_type"),
        media_file_id=data.get("media_file_id"),
        description=data.get("description"),
    )

    author_line = "Анонимно" if suggestion.is_anonymous else f"@{user.username or user.id}"
    mod_caption = (
        f"🔹 Новое предложение #{suggestion.id}\n"
        f"Автор: {author_line}\n\n"
        f"{suggestion.description or ''}"
    )
    media_type, file_id = suggestion.media_type, suggestion.media_file_id
    if media_type == "photo":
        sent = await bot.send_photo(
            settings.MODERATOR_CHAT_ID, file_id, caption=mod_caption, reply_markup=mod_queue_kb(suggestion.id)
        )
    elif media_type == "video":
        sent = await bot.send_video(
            settings.MODERATOR_CHAT_ID, file_id, caption=mod_caption, reply_markup=mod_queue_kb(suggestion.id)
        )
    elif media_type == "document":
        sent = await bot.send_document(
            settings.MODERATOR_CHAT_ID, file_id, caption=mod_caption, reply_markup=mod_queue_kb(suggestion.id)
        )
    else:
        sent = await bot.send_message(
            settings.MODERATOR_CHAT_ID, mod_caption, reply_markup=mod_queue_kb(suggestion.id)
        )

    await set_suggestion_mod_message(suggestion.id, sent.message_id)
    await touch_suggestion_cooldown(user.id)
    await state.clear()

    await callback.message.answer(SUGGEST_SENT.format(cooldown=settings.SUGGESTION_COOLDOWN_MINUTES))
    await callback.answer("Отправлено!")
