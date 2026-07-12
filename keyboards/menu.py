from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def main_menu_kb() -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text="🔥 Актуальное", callback_data="menu:actual")],
        [InlineKeyboardButton(text="🔔 Уведомления", callback_data="menu:notifications")],
        [InlineKeyboardButton(text="🔦 Поделиться", callback_data="menu:share")],
        [InlineKeyboardButton(text="💰 Розыгрыш", callback_data="menu:raffle")],
        [InlineKeyboardButton(text="🔗 Ссылки", callback_data="menu:content")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def back_kb(target: str = "menu:main") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="◀️ Назад", callback_data=target)]]
    )


def with_back(rows: list[list[InlineKeyboardButton]], target: str = "menu:main") -> InlineKeyboardMarkup:
    rows = rows + [[InlineKeyboardButton(text="◀️ Назад", callback_data=target)]]
    return InlineKeyboardMarkup(inline_keyboard=rows)
