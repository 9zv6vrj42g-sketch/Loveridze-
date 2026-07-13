"""
Every user-facing screen in the bot goes through render_screen() so all of
them look and behave the same way:
  - a random photo OR sticker from the library (never the same one twice
    in a row for the same user)
  - the section text + inline keyboard
  - the previous bot message(s) in this chat get deleted first

Telegram stickers can't carry a caption or inline keyboard, so when the
library hands back a sticker, it's sent as its own message and the text +
buttons follow right after as a second message. Both get cleaned up next
time a screen is rendered for that user.

Add new images/stickers by having an admin use /addimage or /addsticker
(see handlers/admin/images.py) — no code changes needed.
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
    last_extra_message_id = user.last_extra_message_id if user else None

    media = await get_random_image(exclude=last_image)

    for msg_id in (last_message_id, last_extra_message_id):
        if msg_id:
            try:
                await bot.delete_message(chat_id, msg_id)
            except Exception:  # noqa: BLE001 - message may already be gone/too old
                pass

    if media is None:
        # Library is empty (e.g. brand new deployment) — fall back to text
        # so the bot still works while an admin fills the library.
        msg = await bot.send_message(chat_id, caption, reply_markup=keyboard)
        await update_last_shown(chat_id, msg.message_id, None, None)
        return msg

    file_id, media_type = media

    if media_type == "sticker":
        sticker_msg = await bot.send_sticker(chat_id, file_id)
        text_msg = await bot.send_message(chat_id, caption, reply_markup=keyboard)
        await update_last_shown(chat_id, text_msg.message_id, file_id, sticker_msg.message_id)
        return text_msg

    photo_msg = await bot.send_photo(chat_id, file_id, caption=caption, reply_markup=keyboard)
    await update_last_shown(chat_id, photo_msg.message_id, file_id, None)
    return photo_msg
