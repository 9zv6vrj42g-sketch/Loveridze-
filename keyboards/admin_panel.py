from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def admin_panel_kb() -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text="📊 Статистика", callback_data="adminpanel:stats")],
        [InlineKeyboardButton(text="👤 Пользователи", callback_data="adminpanel:users")],
        [InlineKeyboardButton(text="🎉 Розыгрыш", callback_data="adminpanel:raffle")],
        [InlineKeyboardButton(text="❗️ Актуальное", callback_data="adminpanel:actual")],
        [InlineKeyboardButton(text="📢 Рассылка", callback_data="adminpanel:broadcast")],
        [InlineKeyboardButton(text="🖼 Медиа", callback_data="adminpanel:media")],
        [InlineKeyboardButton(text="✖️ Закрыть", callback_data="adminpanel:close")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def users_submenu_kb() -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text="✉️ Написать", callback_data="adminpanel:write")],
        [
            InlineKeyboardButton(text="🚫 Бан", callback_data="adminpanel:ban"),
            InlineKeyboardButton(text="♻️ Разбан", callback_data="adminpanel:unban"),
        ],
        [InlineKeyboardButton(text="ℹ️ Инфо о бане", callback_data="adminpanel:baninfo")],
        [
            InlineKeyboardButton(text="🔇 Мьют", callback_data="adminpanel:mute"),
            InlineKeyboardButton(text="🔊 Размьют", callback_data="adminpanel:unmute"),
        ],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="adminpanel:main")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def raffle_submenu_kb() -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text="🆕 Создать розыгрыш", callback_data="adminpanel:givestart")],
        [InlineKeyboardButton(text="ℹ️ Текущий розыгрыш", callback_data="adminpanel:giveinfo")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="adminpanel:main")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def media_submenu_kb() -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text="🖼 Добавить фото", callback_data="adminpanel:addimage")],
        [InlineKeyboardButton(text="🎭 Добавить стикер", callback_data="adminpanel:addsticker")],
        [InlineKeyboardButton(text="🔢 Счётчик", callback_data="adminpanel:imagescount")],
        [InlineKeyboardButton(text="🗑 Удалить", callback_data="adminpanel:imagedelete")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="adminpanel:main")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def back_to_panel_kb(target: str = "adminpanel:main") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="◀️ Назад", callback_data=target)]]
    )
