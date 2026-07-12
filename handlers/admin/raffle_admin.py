from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from config import settings
from database.requests import (
    count_participants,
    create_raffle,
    delete_raffle,
    edit_raffle,
    get_active_raffle,
    get_raffle,
    start_raffle,
)
from keyboards.raffle import raffle_admin_preview_kb, raffle_edit_fields_kb
from utils.states import RaffleCreateStates, RaffleEditStates

router = Router(name="admin_raffle")


def _admin_only(message_or_callback) -> bool:
    return message_or_callback.from_user.id in settings.admin_ids


async def _preview_text(raffle) -> str:
    participants = await count_participants(raffle.id)
    status = "🟢 Активный" if raffle.status == "active" else "⚪️ Неактивный"
    return (
        f"Предпросмотр розыгрыша\n\n"
        f"Номер: {raffle.number}\n"
        f"Название: {raffle.title}\n"
        f"Описание: {raffle.description}\n"
        f"Победителей: {raffle.winners_count}\n"
        f"Длительность: {raffle.duration_hours} ч\n"
        f"Статус: {status}\n"
        f"🙆🏼\u200d♂️ Участников: {participants}"
    )


# ------------------------------------------------------------- /givestart --
@router.message(Command("givestart"))
async def cmd_givestart(message: Message, state: FSMContext) -> None:
    if not _admin_only(message):
        return
    await state.set_state(RaffleCreateStates.number)
    await message.answer("Шаг 1/5. Укажи номер розыгрыша (число):")


@router.message(RaffleCreateStates.number, F.text)
async def givestart_number(message: Message, state: FSMContext) -> None:
    if not message.text.strip().lstrip("-").isdigit():
        await message.answer("Номер должен быть числом. Попробуй еще раз:")
        return
    await state.update_data(number=int(message.text.strip()))
    await state.set_state(RaffleCreateStates.title)
    await message.answer("Шаг 2/5. Название розыгрыша:")


@router.message(RaffleCreateStates.title, F.text)
async def givestart_title(message: Message, state: FSMContext) -> None:
    await state.update_data(title=message.text.strip())
    await state.set_state(RaffleCreateStates.description)
    await message.answer("Шаг 3/5. Описание розыгрыша:")


@router.message(RaffleCreateStates.description, F.text)
async def givestart_description(message: Message, state: FSMContext) -> None:
    await state.update_data(description=message.text.strip())
    await state.set_state(RaffleCreateStates.winners_count)
    await message.answer("Шаг 4/5. Количество победителей (число):")


@router.message(RaffleCreateStates.winners_count, F.text)
async def givestart_winners(message: Message, state: FSMContext) -> None:
    if not message.text.strip().isdigit():
        await message.answer("Нужно число. Попробуй еще раз:")
        return
    await state.update_data(winners_count=int(message.text.strip()))
    await state.set_state(RaffleCreateStates.hours)
    await message.answer("Шаг 5/5. Время до окончания розыгрыша, в часах (число):")


@router.message(RaffleCreateStates.hours, F.text)
async def givestart_hours(message: Message, state: FSMContext) -> None:
    if not message.text.strip().isdigit():
        await message.answer("Нужно число. Попробуй еще раз:")
        return
    data = await state.get_data()
    hours = int(message.text.strip())

    raffle = await create_raffle(
        number=data["number"],
        title=data["title"],
        description=data["description"],
        winners_count=data["winners_count"],
        hours=hours,
    )
    await state.clear()
    await state.update_data(raffle_id=raffle.id)
    text = await _preview_text(raffle)
    await message.answer(text, reply_markup=raffle_admin_preview_kb())


# --------------------------------------------------------------- /giveinfo --
@router.message(Command("giveinfo"))
async def cmd_giveinfo(message: Message, state: FSMContext) -> None:
    if not _admin_only(message):
        return
    raffle = await get_active_raffle()
    if raffle is None:
        await message.answer("Нет активного розыгрыша. Создай его командой /givestart")
        return
    await state.update_data(raffle_id=raffle.id)
    text = await _preview_text(raffle)
    await message.answer(text, reply_markup=raffle_admin_preview_kb())


# ------------------------------------------------------- preview callbacks --
@router.callback_query(F.data == "raffleadmin:start")
async def raffleadmin_start(callback: CallbackQuery, state: FSMContext) -> None:
    if not _admin_only(callback):
        await callback.answer("Только для администрации", show_alert=True)
        return
    data = await state.get_data()
    raffle_id = data.get("raffle_id")
    await start_raffle(raffle_id)
    raffle = await get_raffle(raffle_id)
    text = await _preview_text(raffle)
    await callback.message.edit_text(text, reply_markup=raffle_admin_preview_kb())
    await callback.answer("Розыгрыш запущен ✅")


@router.callback_query(F.data == "raffleadmin:delete")
async def raffleadmin_delete(callback: CallbackQuery, state: FSMContext) -> None:
    if not _admin_only(callback):
        await callback.answer("Только для администрации", show_alert=True)
        return
    data = await state.get_data()
    raffle_id = data.get("raffle_id")
    await delete_raffle(raffle_id)
    await state.clear()
    await callback.message.edit_text("❌ Розыгрыш удален.")
    await callback.answer()


@router.callback_query(F.data == "raffleadmin:edit")
async def raffleadmin_edit(callback: CallbackQuery) -> None:
    if not _admin_only(callback):
        await callback.answer("Только для администрации", show_alert=True)
        return
    await callback.message.edit_text("🔸 Edit — что изменить?", reply_markup=raffle_edit_fields_kb())
    await callback.answer()


@router.callback_query(F.data == "raffleadmin:back_to_preview")
async def raffleadmin_back_to_preview(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    raffle = await get_raffle(data.get("raffle_id"))
    text = await _preview_text(raffle)
    await callback.message.edit_text(text, reply_markup=raffle_admin_preview_kb())
    await callback.answer()


@router.callback_query(F.data.startswith("raffleedit:"))
async def raffleedit_choose_field(callback: CallbackQuery, state: FSMContext) -> None:
    field = callback.data.split(":")[-1]
    await state.update_data(edit_field=field)
    await state.set_state(RaffleEditStates.waiting_value)
    prompts = {
        "title": "Отправь новое название/описание:",
        "winners": "Отправь новое количество победителей (число):",
        "hours": "Отправь новое время в часах (число):",
    }
    await callback.message.answer(prompts.get(field, "Отправь новое значение:"))
    await callback.answer()


@router.message(RaffleEditStates.waiting_value, F.text)
async def raffleedit_receive_value(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    field = data.get("edit_field")
    raffle_id = data.get("raffle_id")

    if field == "title":
        await edit_raffle(raffle_id, title=message.text.strip(), description=message.text.strip())
    elif field == "winners":
        if not message.text.strip().isdigit():
            await message.answer("Нужно число.")
            return
        await edit_raffle(raffle_id, winners_count=int(message.text.strip()))
    elif field == "hours":
        if not message.text.strip().isdigit():
            await message.answer("Нужно число.")
            return
        await edit_raffle(raffle_id, duration_hours=int(message.text.strip()))

    await state.set_state(None)
    raffle = await get_raffle(raffle_id)
    text = await _preview_text(raffle)
    await message.answer(text, reply_markup=raffle_admin_preview_kb())
