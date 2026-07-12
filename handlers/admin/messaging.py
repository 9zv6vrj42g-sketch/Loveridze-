import datetime as dt

from aiogram import F, Router
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from config import settings
from database.requests import find_user_by_username, get_user, set_ban, set_mute
from utils.states import ModerationCommentStates

router = Router(name="admin_messaging")


def _admin_only(message: Message) -> bool:
    return message.from_user.id in settings.admin_ids


async def _resolve_target(token: str) -> int | None:
    token = token.strip()
    if token.startswith("@"):
        user = await find_user_by_username(token)
        return user.id if user else None
    if token.lstrip("-").isdigit():
        return int(token)
    return None


# ------------------------------------------------------------------ /write --
@router.message(Command("write"))
async def cmd_write(message: Message, command: CommandObject, bot) -> None:
    if not _admin_only(message):
        return
    if not command.args:
        await message.answer("Использование: /write id текст  или  /write @username текст")
        return
    parts = command.args.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("Нужно указать текст сообщения.")
        return
    target_token, text = parts
    target_id = await _resolve_target(target_token)
    if target_id is None:
        await message.answer("Пользователь не найден.")
        return
    try:
        await bot.send_message(target_id, text)
        await message.answer("✅ Отправлено.")
    except Exception as exc:  # noqa: BLE001
        await message.answer(f"⚠️ Не удалось отправить: {exc}")


# -------------------------------------------------------------------- /ban --
@router.message(Command("ban"))
async def cmd_ban(message: Message, command: CommandObject, state: FSMContext) -> None:
    if not _admin_only(message):
        return
    if not command.args:
        await message.answer("Использование: /ban @username  или  /ban id")
        return
    target_id = await _resolve_target(command.args.strip())
    if target_id is None:
        await message.answer("Пользователь не найден.")
        return
    await set_ban(target_id, True)
    await state.update_data(comment_action="ban", comment_target=target_id)
    await state.set_state(ModerationCommentStates.waiting_comment)
    await message.answer("Пользователь забанен ✅\nНапиши комментарий с причиной (или отправь «-» чтобы пропустить).")


@router.message(Command("unban"))
async def cmd_unban(message: Message, command: CommandObject) -> None:
    if not _admin_only(message):
        return
    if not command.args:
        await message.answer("Использование: /unban @username  или  /unban id")
        return
    target_id = await _resolve_target(command.args.strip())
    if target_id is None:
        await message.answer("Пользователь не найден.")
        return
    await set_ban(target_id, False, comment=None)
    await message.answer("Пользователь разбанен ✅")


@router.message(Command("baninfo"))
async def cmd_baninfo(message: Message, command: CommandObject) -> None:
    if not _admin_only(message):
        return
    if not command.args:
        await message.answer("Использование: /baninfo @username  или  /baninfo id")
        return
    target_id = await _resolve_target(command.args.strip())
    if target_id is None:
        await message.answer("Пользователь не найден.")
        return
    user = await get_user(target_id)
    if not user or not user.is_banned:
        await message.answer("Пользователь не забанен.")
        return
    await message.answer(f"🚫 Забанен.\nКомментарий: {user.ban_comment or '—'}")


# ------------------------------------------------------------------- /mute --
@router.message(Command("mute"))
async def cmd_mute(message: Message, command: CommandObject, state: FSMContext) -> None:
    if not _admin_only(message):
        return
    if not command.args:
        await message.answer("Использование: /mute @username минут  или  /mute id минут")
        return
    parts = command.args.split()
    target_token = parts[0]
    minutes = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 60
    target_id = await _resolve_target(target_token)
    if target_id is None:
        await message.answer("Пользователь не найден.")
        return
    until = dt.datetime.utcnow() + dt.timedelta(minutes=minutes)
    await set_mute(target_id, until)
    await state.update_data(comment_action="mute", comment_target=target_id)
    await state.set_state(ModerationCommentStates.waiting_comment)
    await message.answer(
        f"Пользователь замьючен на {minutes} мин ✅\nНапиши комментарий с причиной (или «-» чтобы пропустить)."
    )


@router.message(Command("unmute"))
async def cmd_unmute(message: Message, command: CommandObject) -> None:
    if not _admin_only(message):
        return
    if not command.args:
        await message.answer("Использование: /unmute @username  или  /unmute id")
        return
    target_id = await _resolve_target(command.args.strip())
    if target_id is None:
        await message.answer("Пользователь не найден.")
        return
    await set_mute(target_id, None, comment=None)
    await message.answer("Мьют снят ✅")


@router.message(ModerationCommentStates.waiting_comment, F.text)
async def receive_moderation_comment(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    target_id = data.get("comment_target")
    action = data.get("comment_action")
    comment = None if message.text.strip() == "-" else message.text.strip()

    if action == "ban":
        await set_ban(target_id, True, comment=comment)
    elif action == "mute":
        user = await get_user(target_id)
        await set_mute(target_id, user.muted_until if user else None, comment=comment)

    await state.clear()
    await message.answer("Комментарий сохранен ✅" if comment else "Ок, без комментария.")
