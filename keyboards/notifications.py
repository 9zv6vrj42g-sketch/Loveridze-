from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def notifications_kb(current_on: bool) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text=("🔔 Включить уведомления" if not current_on else "🔔 Включено ✓"),
                callback_data="notif:on",
            )
        ],
        [
            InlineKeyboardButton(
                text=("🔕 Отключить уведомления" if current_on else "🔕 Отключено ✓"),
                callback_data="notif:off",
            )
        ],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="menu:main")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)
