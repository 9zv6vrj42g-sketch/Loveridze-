"""
Every user-facing screen in the bot goes through render_screen() so all of
them look and behave the same way:
  - a random image from the library (never the same one twice in a row)
  - the section text as the photo caption
  - inline keyboard underneath
  - the previous bot message in this chat gets deleted first

Add new images by having an admin send a photo to the bot with the
/addimage command (see handlers/admin/images.py) — no code changes needed.
"""
from __future__ import annotations

from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, Message

from database.requests import get_random_image, get_user, update_last_shown


async def render_screen(
    bot: Bot,
    chat_id: int,
    caption: str,
    keyboard: InlineKeyboardMarkup,
) -> Message:
    user = await get_user(chat_id)
    last_image = user.last_image_id if user else None
    last_message_id = user.last_message_id if user else None

    image_id = await get_random_image(exclude=last_image)

    if last_message_id:
        try:
            await bot.delete_message(chat_id, last_message_id)
        except Exception:  # noqa: BLE001 - message may already be gone/too old
            pass

    if image_id:
        msg = await bot.send_photo(chat_id, image_id, caption=caption, reply_markup=keyboard)
    else:
        # Library is empty (e.g. brand new deployment) — fall back to text
        # so the bot still works while an admin fills the library via /addimage.
        msg = await bot.send_message(chat_id, caption, reply_markup=keyboard)

    await update_last_shown(chat_id, msg.message_id, image_id)
    return msg
