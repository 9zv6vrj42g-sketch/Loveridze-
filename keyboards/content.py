from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from config import settings


def content_kb() -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(text="⌁ TikTok Основной", url=settings.TIKTOK_MAIN_LINK),
            InlineKeyboardButton(text="⌁ TikTok Фан канал", url=settings.TIKTOK_FAN_LINK),
        ],
        [InlineKeyboardButton(text="⌁ Instagram", url=settings.INSTAGRAM_LINK)],
        [InlineKeyboardButton(text="⌁ YouTube", url=settings.YOUTUBE_LINK)],
        [InlineKeyboardButton(text="⌁ Threads", url=settings.THREADS_LINK)],
        [InlineKeyboardButton(text="⌁ X", url=settings.X_LINK)],
        [InlineKeyboardButton(text="⌁ 18+", url=settings.ADULT_LINK)],
        [InlineKeyboardButton(text="↩️ Назад", callback_data="menu:main")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)
