from urllib.parse import quote

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def _share_url(link: str, text: str) -> str:
    return f"https://t.me/share/url?url={quote(link, safe='')}&text={quote(text, safe='')}"


def share_kb(bot_link: str, channel_link: str, group_link: str) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text="🤖 Поделиться ботом", url=_share_url(bot_link, "Загляни сюда 👇"))],
        [InlineKeyboardButton(text="📢 Поделиться каналом", url=_share_url(channel_link, "Наш канал 👇"))],
        [InlineKeyboardButton(text="👥 Поделиться группой", url=_share_url(group_link, "Наша группа 👇"))],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="menu:main")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)
