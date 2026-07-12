from __future__ import annotations

from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

from config import settings
from database.requests import get_user
from utils.texts import BANNED_MESSAGE


class PrivateOnlyMiddleware(BaseMiddleware):
    """Bot only responds in private chats — everything else is ignored,
    except messages sent inside the moderator chat, which the moderation
    handlers need to see."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        message = event if isinstance(event, Message) else None
        if message is not None and message.chat.id == settings.MODERATOR_CHAT_ID:
            return await handler(event, data)

        chat = None
        if isinstance(event, Message):
            chat = event.chat
        elif isinstance(event, CallbackQuery) and event.message:
            chat = event.message.chat

        if chat is not None and chat.type != "private":
            return None

        return await handler(event, data)


class AccessControlMiddleware(BaseMiddleware):
    """Blocks banned users entirely, and muted users from sending suggestions/
    raffle proofs (admin commands & menu browsing still work for muted users)."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user = None
        if isinstance(event, Message):
            user = event.from_user
        elif isinstance(event, CallbackQuery):
            user = event.from_user

        if user is None or user.id in settings.admin_ids:
            return await handler(event, data)

        db_user = await get_user(user.id)
        if db_user and db_user.is_banned:
            if isinstance(event, Message):
                await event.answer(BANNED_MESSAGE)
            elif isinstance(event, CallbackQuery):
                await event.answer(BANNED_MESSAGE, show_alert=True)
            return None

        return await handler(event, data)
