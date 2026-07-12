from aiogram import F, Router
from aiogram.types import CallbackQuery

from config import settings
from keyboards.share import share_kb
from utils.screens import render_screen

router = Router(name="share")

_bot_link_cache: dict[str, str] = {}


async def _get_bot_link(bot) -> str:
    cached = _bot_link_cache.get("link")
    if cached:
        return cached
    me = await bot.get_me()
    link = f"https://t.me/{me.username}"
    _bot_link_cache["link"] = link
    return link


@router.callback_query(F.data == "menu:share")
async def show_share(callback: CallbackQuery) -> None:
    bot_link = await _get_bot_link(callback.bot)
    text = "🔦 Поделиться\n\nВыбери, чем хочешь поделиться:"
    await render_screen(
        callback.bot,
        callback.message.chat.id,
        text,
        share_kb(bot_link, settings.CHANNEL_LINK, settings.GROUP_LINK),
    )
    await callback.answer()
