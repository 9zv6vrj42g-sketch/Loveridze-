import datetime as dt

from aiogram import Bot, Router
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


async def build_stats_text(bot: Bot) -> str:
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
        channel_members = "—"
    try:
        group_members = await bot.get_chat_member_count(settings.GROUP_ID)
    except Exception:  # noqa: BLE001
        group_members = "—"

    return (
        "📊 Статистика\n\n"
        f"▫️ Бот: {bot_users}\n"
        f"▫️ Канал: {channel_members}\n"
        f"▫️ Группа: {group_members}\n\n"
        f"🔹 1 DAY: {day_diff}\n"
        f"🔹 1 WEEK: {week_diff}\n"
        f"🔹 1 MONTH: {month_diff}\n\n"
        f"🚫 Banned: {banned_count}\n"
        f"🔸 Всего розыгрышей: {total_raffles}\n\n"
        f"✉️ Последняя рассылка (/notsend): {last_broadcast}\n"
        f"🔔 Уведомления вкл: {notif_on}\n"
        f"🔕 Уведомления выкл: {notif_off}"
    )


@router.message(Command("stats"))
async def cmd_stats(message: Message, bot: Bot) -> None:
    if message.from_user.id not in settings.admin_ids:
        return
    await message.answer(await build_stats_text(bot))
