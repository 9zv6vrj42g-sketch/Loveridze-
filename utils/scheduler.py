from __future__ import annotations

import datetime as dt
import random

from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config import settings
from database.engine import async_session
from database.models import Raffle
from database.requests import (
    finish_raffle,
    get_participants,
    set_active_winners,
)
from sqlalchemy import select


async def _close_expired_raffles(bot: Bot) -> None:
    now = dt.datetime.utcnow()
    async with async_session() as session:
        result = await session.execute(
            select(Raffle).where(Raffle.status == "active", Raffle.ends_at <= now)
        )
        expired = list(result.scalars().all())

    for raffle in expired:
        participants = await get_participants(raffle.id)
        winners = random.sample(participants, k=min(raffle.winners_count, len(participants))) if participants else []
        winner_ids = [p.user_id for p in winners]
        if winner_ids:
            await set_active_winners(raffle.id, winner_ids)

        result_lines = [f"Розыгрыш №{raffle.number} «{raffle.title}» завершен."]
        result_lines.append(f"Участников: {len(participants)}")
        if winner_ids:
            result_lines.append("Победители: " + ", ".join(str(uid) for uid in winner_ids))
        else:
            result_lines.append("Победители не определены (не было участников).")
        result_message = "\n".join(result_lines)

        await finish_raffle(raffle.id, result_message)

        try:
            await bot.send_message(settings.MODERATOR_CHAT_ID, f"🔸 {result_message}")
        except Exception:  # noqa: BLE001
            pass

        for uid in winner_ids:
            try:
                await bot.send_message(
                    uid,
                    f"🎉 Поздравляем! Ты победитель розыгрыша №{raffle.number} «{raffle.title}»!",
                )
            except Exception:  # noqa: BLE001
                pass


def setup_scheduler(bot: Bot) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone=settings.TIMEZONE)
    scheduler.add_job(_close_expired_raffles, "interval", minutes=1, args=[bot], id="close_expired_raffles")
    scheduler.start()
    return scheduler
