from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def raffle_active_kb(raffle_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Участвовать", callback_data=f"raffle:join:{raffle_id}"),
                InlineKeyboardButton(text="📊 Статистика", callback_data="raffle:stats"),
            ],
            [InlineKeyboardButton(text="🔔 Уведомления", callback_data="raffle:notifications")],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="menu:main")],
        ]
    )


def raffle_idle_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📊 Статистика", callback_data="raffle:stats")],
            [InlineKeyboardButton(text="🔔 Уведомления", callback_data="raffle:notifications")],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="menu:main")],
        ]
    )


def raffle_stats_kb(current_number: int, prev_number: int | None, next_number: int | None) -> InlineKeyboardMarkup:
    nav_row = []
    if prev_number is not None:
        nav_row.append(InlineKeyboardButton(text="👈 Предыдущий", callback_data=f"raffle:stats_view:{prev_number}"))
    if next_number is not None:
        nav_row.append(InlineKeyboardButton(text="👉 Следующий", callback_data=f"raffle:stats_view:{next_number}"))
    rows = []
    if nav_row:
        rows.append(nav_row)
    rows.append([InlineKeyboardButton(text="◀️ Назад", callback_data="menu:raffle")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def raffle_admin_preview_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Start", callback_data="raffleadmin:start")],
            [
                InlineKeyboardButton(text="🔸 Edit", callback_data="raffleadmin:edit"),
                InlineKeyboardButton(text="❌ Удалить", callback_data="raffleadmin:delete"),
            ],
        ]
    )


def raffle_edit_fields_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Название", callback_data="raffleedit:title")],
            [InlineKeyboardButton(text="Количество победителей", callback_data="raffleedit:winners")],
            [InlineKeyboardButton(text="Время (часы)", callback_data="raffleedit:hours")],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="raffleadmin:back_to_preview")],
        ]
    )
