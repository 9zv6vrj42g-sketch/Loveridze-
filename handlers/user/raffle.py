import datetime as dt

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from config import settings

from database.requests import (
    add_raffle_participant,
    count_all_raffles,
    count_participants,
    get_active_raffle,
    get_last_raffle,
    get_raffle,
    get_raffle_by_number,
    get_raffle_neighbors,
    is_raffle_participant,
)
from keyboards.menu import back_kb
from keyboards.raffle import raffle_active_kb, raffle_idle_kb, raffle_stats_kb
from utils.screens import render_screen
from utils.states import RaffleJoinStates
from utils.texts import RAFFLE_JOIN_PROMPT, RAFFLE_JOINED, RAFFLE_LAST_RESULTS_HEADER, RAFFLE_NOT_STARTED

router = Router(name="raffle")


def _format_time_left(ends_at: dt.datetime | None) -> str:
    if ends_at is None:
        return "—"
    remaining = ends_at - dt.datetime.utcnow()
    if remaining.total_seconds() <= 0:
        return "0 мин"
    hours, rem = divmod(int(remaining.total_seconds()), 3600)
    minutes = rem // 60
    if hours:
        return f"{hours} ч {minutes} мин"
    return f"{minutes} мин"


@router.callback_query(F.data == "menu:raffle")
async def show_raffle(callback: CallbackQuery) -> None:
    active = await get_active_raffle()
    if active:
        participants = await count_participants(active.id)
        text = (
            f"💰 Розыгрыш\n\n"
            f"🟢 «{active.title}»\n"
            f"{active.description}\n\n"
            f"👥 Участников: {participants}\n"
            f"⏳ Осталось: {_format_time_left(active.ends_at)}"
        )
        await render_screen(callback.bot, callback.message.chat.id, text, raffle_active_kb(active.id))
    else:
        last = await get_last_raffle()
        text = f"💰 Розыгрыш\n\n{RAFFLE_NOT_STARTED}"
        if last and last.status == "finished":
            text += f"\n\n{RAFFLE_LAST_RESULTS_HEADER}\n{last.result_message or '—'}"
        await render_screen(callback.bot, callback.message.chat.id, text, raffle_idle_kb())
    await callback.answer()


@router.callback_query(F.data.startswith("raffle:join:"))
async def raffle_join_start(callback: CallbackQuery, state: FSMContext) -> None:
    raffle_id = int(callback.data.split(":")[-1])
    if await is_raffle_participant(raffle_id, callback.from_user.id):
        await callback.answer("Ты уже участвуешь в этом розыгрыше", show_alert=True)
        return
    await state.update_data(raffle_id=raffle_id)
    await state.set_state(RaffleJoinStates.waiting_proof)
    await render_screen(callback.bot, callback.message.chat.id, RAFFLE_JOIN_PROMPT, back_kb("menu:raffle"))
    await callback.answer()


@router.message(RaffleJoinStates.waiting_proof, F.text)
async def raffle_join_proof(message: Message, state: FSMContext, bot) -> None:
    data = await state.get_data()
    raffle_id = data.get("raffle_id")
    raffle = await get_raffle(raffle_id)
    if raffle is None or raffle.status != "active":
        await render_screen(bot, message.chat.id, "Этот розыгрыш уже недоступен.", back_kb("menu:raffle"))
        await state.clear()
        return

    await add_raffle_participant(raffle_id, message.from_user.id, message.text)
    participants = await count_participants(raffle_id)
    chance = round(100 * raffle.winners_count / max(participants, 1), 1)

    await state.clear()
    joined_text = RAFFLE_JOINED.format(
        number=raffle.number,
        title=raffle.title,
        description=raffle.description,
        participants=participants,
        chance=chance,
        time_left=_format_time_left(raffle.ends_at),
    )
    await render_screen(bot, message.chat.id, joined_text, back_kb("menu:raffle"))

    author = f"@{message.from_user.username}" if message.from_user.username else str(message.from_user.id)
    await bot.send_message(
        settings.MODERATOR_CHAT_ID,
        f"💰 Розыгрыш №{raffle.number}\nУчастник: {author}\nПруф: {message.text}",
    )


@router.callback_query(F.data == "raffle:stats")
async def raffle_stats(callback: CallbackQuery) -> None:
    total = await count_all_raffles()
    last = await get_last_raffle()
    if last is None:
        await render_screen(
            callback.bot, callback.message.chat.id, "Розыгрышей еще не было.", back_kb("menu:raffle")
        )
        await callback.answer()
        return
    await _render_stats(callback, last.number, total)


@router.callback_query(F.data.startswith("raffle:stats_view:"))
async def raffle_stats_view(callback: CallbackQuery) -> None:
    number = int(callback.data.split(":")[-1])
    total = await count_all_raffles()
    await _render_stats(callback, number, total)


async def _render_stats(callback: CallbackQuery, number: int, total: int) -> None:
    raffle = await get_raffle_by_number(number)
    if raffle is None:
        await callback.answer("Розыгрыш не найден", show_alert=True)
        return
    participants = await count_participants(raffle.id)
    prev_n, next_n = await get_raffle_neighbors(number)

    text = (
        f"📊 Статистика\n\n"
        f"Всего проведено 💰 {total}\n\n"
        f"▫️ Розыгрыш №{raffle.number}\n"
        f"«{raffle.title}»\n"
        f"{raffle.description}\n\n"
        f"👥 Участников: {participants}\n"
        f"Статус: {raffle.status}\n"
    )
    if raffle.result_message:
        text += f"\nРезультат:\n{raffle.result_message}"

    await render_screen(callback.bot, callback.message.chat.id, text, raffle_stats_kb(number, prev_n, next_n))
    await callback.answer()
