from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def suggest_mode_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="☑️ Анонимно", callback_data="suggest:mode:anon"),
                InlineKeyboardButton(text="✅ Публично", callback_data="suggest:mode:public"),
            ],
            [InlineKeyboardButton(text="↩️ Назад", callback_data="menu:main")],
        ]
    )


def suggest_media_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="↪️ Дальше", callback_data="suggest:next")],
            [InlineKeyboardButton(text="↩️ Назад", callback_data="menu:main")],
        ]
    )


def suggest_description_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="↪️ Дальше", callback_data="suggest:next")],
            [InlineKeyboardButton(text="↩️ Назад", callback_data="suggest:back_to_media")],
        ]
    )


def suggest_preview_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Отправить", callback_data="suggest:submit"),
                InlineKeyboardButton(text="↪️ Редактировать", callback_data="suggest:edit"),
            ],
        ]
    )


def mod_queue_kb(suggestion_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Одобрить", callback_data=f"mod:approve:{suggestion_id}"),
                InlineKeyboardButton(text="❌ Отклонить", callback_data=f"mod:reject:{suggestion_id}"),
            ]
        ]
    )
