import datetime as dt

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from config import settings
from database.requests import (
    count_all_raffles,
    count_banned,
    count_notifications,
    count_users_since,
    count_users_total,
    get_last_broadcast_count,
)

router = Router(name="admin_stats")


@router.message(Command("stats"))
async def cmd_stats(message: Message, bot) -> None:
    if message.from_user.id not in settings.admin_ids:
        return

    now = dt.datetime.utcnow()
    bot_users = await count_users_total()
    day_diff = await count_users_since(now - dt.timedelta(days=1))
    week_diff = await count_users_since(now - dt.timedelta(weeks=1))
    month_diff = await count_users_since(now - dt.timedelta(days=30))
    banned_count = await count_banned()
    total_raffles = await count_all_raffles()
    notif_on = await count_notifications(True)
    notif_off = await count_notifications(False)
    last_broadcast = await get_last_broadcast_count()

    try:
        channel_members = await bot.get_chat_member_count(settings.CHANNEL_ID)
    except Exception:  # noqa: BLE001
        channel_members = "â"
    try:
        group_members = await bot.get_chat_member_count(settings.GROUP_ID)
    except Exception:  # noqa: BLE001
        group_members = "â"

    text = (
        "ð Ð¡ÑÐ°ÑÐ¸ÑÑÐ¸ÐºÐ°\n\n"
        f"â«ï¸ ÐÐ¾Ñ: {bot_users}\n"
        f"â«ï¸ ÐÐ°Ð½Ð°Ð»: {channel_members}\n"
        f"â«ï¸ ÐÑÑÐ¿Ð¿Ð°: {group_members}\n\n"
        f"ð¹ 1 DAY: {day_diff}\n"
        f"ð¹ 1 WEEK: {week_diff}\n"
        f"ð¹ 1 MONTH: {month_diff}\n\n"
        f"ð« Banned: {banned_count}\n"
        f"ð¸ ÐÑÐµÐ³Ð¾ ÑÐ¾Ð·ÑÐ³ÑÑÑÐµÐ¹: {total_raffles}\n\n"
        f"âï¸ ÐÐ¾ÑÐ»ÐµÐ´Ð½ÑÑ ÑÐ°ÑÑÑÐ»ÐºÐ° (/notsend): {last_broadcast}\n"
        f"ð Ð£Ð²ÐµÐ´Ð¾Ð¼Ð»ÐµÐ½Ð¸Ñ Ð²ÐºÐ»: {notif_on}\n"
        f"ð Ð£Ð²ÐµÐ´Ð¾Ð¼Ð»ÐµÐ½Ð¸Ñ Ð²ÑÐºÐ»: {notif_off}"
    )
    await message.answer(text)
