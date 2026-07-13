from __future__ import annotations

import datetime as dt

from sqlalchemy import func, select, update

from config import settings
from database.engine import async_session
from database.models import ActualInfo, BroadcastLog, ImageLibrary, Raffle, RaffleParticipant, Suggestion, User


# ------------------------------------------------------------------ users --
async def get_or_create_user(user_id: int, username: str | None, full_name: str | None) -> User:
    async with async_session() as session:
        user = await session.get(User, user_id)
        if user is None:
            user = User(id=user_id, username=username, full_name=full_name)
            session.add(user)
            await session.commit()
            await session.refresh(user)
        elif user.username != username or user.full_name != full_name:
            user.username = username
            user.full_name = full_name
            await session.commit()
        return user


async def get_user(user_id: int) -> User | None:
    async with async_session() as session:
        return await session.get(User, user_id)


async def find_user_by_username(username: str) -> User | None:
    username = username.lstrip("@")
    async with async_session() as session:
        result = await session.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()


async def set_notifications(user_id: int, on: bool) -> None:
    async with async_session() as session:
        await session.execute(update(User).where(User.id == user_id).values(notifications_on=on))
        await session.commit()


async def set_ban(user_id: int, banned: bool, comment: str | None = None) -> None:
    async with async_session() as session:
        await session.execute(
            update(User).where(User.id == user_id).values(is_banned=banned, ban_comment=comment)
        )
        await session.commit()


async def set_mute(user_id: int, until: dt.datetime | None, comment: str | None = None) -> None:
    async with async_session() as session:
        await session.execute(
            update(User).where(User.id == user_id).values(muted_until=until, mute_comment=comment)
        )
        await session.commit()


async def touch_suggestion_cooldown(user_id: int) -> None:
    async with async_session() as session:
        await session.execute(
            update(User).where(User.id == user_id).values(last_suggestion_at=dt.datetime.utcnow())
        )
        await session.commit()


async def notified_user_ids() -> list[int]:
    async with async_session() as session:
        result = await session.execute(select(User.id).where(User.notifications_on.is_(True)))
        return [row[0] for row in result.all()]


async def count_users_total() -> int:
    async with async_session() as session:
        result = await session.execute(select(func.count()).select_from(User))
        return result.scalar_one()


async def count_users_since(since: dt.datetime) -> int:
    async with async_session() as session:
        result = await session.execute(
            select(func.count()).select_from(User).where(User.joined_at >= since)
        )
        return result.scalar_one()


async def count_banned() -> int:
    async with async_session() as session:
        result = await session.execute(
            select(func.count()).select_from(User).where(User.is_banned.is_(True))
        )
        return result.scalar_one()


async def count_notifications(on: bool) -> int:
    async with async_session() as session:
        result = await session.execute(
            select(func.count()).select_from(User).where(User.notifications_on.is_(on))
        )
        return result.scalar_one()


# ------------------------------------------------------------ suggestions --
async def create_suggestion(
    user_id: int,
    is_anonymous: bool,
    media_type: str | None,
    media_file_id: str | None,
    description: str | None,
) -> Suggestion:
    async with async_session() as session:
        suggestion = Suggestion(
            user_id=user_id,
            is_anonymous=is_anonymous,
            media_type=media_type,
            media_file_id=media_file_id,
            description=description,
        )
        session.add(suggestion)
        await session.commit()
        await session.refresh(suggestion)
        return suggestion


async def set_suggestion_mod_message(suggestion_id: int, message_id: int) -> None:
    async with async_session() as session:
        await session.execute(
            update(Suggestion).where(Suggestion.id == suggestion_id).values(mod_chat_message_id=message_id)
        )
        await session.commit()


# ----------------------------------------------------------------- raffle --
async def create_raffle(number: int, title: str, description: str, winners_count: int, hours: int) -> Raffle:
    async with async_session() as session:
        raffle = Raffle(
            number=number,
            title=title,
            description=description,
            winners_count=winners_count,
            duration_hours=hours,
        )
        session.add(raffle)
        await session.commit()
        await session.refresh(raffle)
        return raffle


async def get_raffle(raffle_id: int) -> Raffle | None:
    async with async_session() as session:
        return await session.get(Raffle, raffle_id)


async def get_active_raffle() -> Raffle | None:
    async with async_session() as session:
        result = await session.execute(select(Raffle).where(Raffle.status == "active"))
        return result.scalar_one_or_none()


async def get_last_raffle() -> Raffle | None:
    async with async_session() as session:
        result = await session.execute(select(Raffle).order_by(Raffle.id.desc()).limit(1))
        return result.scalar_one_or_none()


async def get_raffle_by_number(number: int) -> Raffle | None:
    async with async_session() as session:
        result = await session.execute(select(Raffle).where(Raffle.number == number))
        return result.scalar_one_or_none()


async def start_raffle(raffle_id: int) -> None:
    now = dt.datetime.utcnow()
    async with async_session() as session:
        raffle = await session.get(Raffle, raffle_id)
        if raffle:
            raffle.status = "active"
            raffle.started_at = now
            raffle.ends_at = now + dt.timedelta(hours=raffle.duration_hours)
            await session.commit()


async def edit_raffle(raffle_id: int, **fields) -> None:
    async with async_session() as session:
        await session.execute(update(Raffle).where(Raffle.id == raffle_id).values(**fields))
        await session.commit()


async def delete_raffle(raffle_id: int) -> None:
    async with async_session() as session:
        raffle = await session.get(Raffle, raffle_id)
        if raffle:
            await session.delete(raffle)
            await session.commit()


async def finish_raffle(raffle_id: int, result_message: str) -> None:
    async with async_session() as session:
        await session.execute(
            update(Raffle)
            .where(Raffle.id == raffle_id)
            .values(status="finished", result_message=result_message)
        )
        await session.commit()


async def add_raffle_participant(raffle_id: int, user_id: int, proof_text: str | None) -> RaffleParticipant:
    async with async_session() as session:
        participant = RaffleParticipant(raffle_id=raffle_id, user_id=user_id, proof_text=proof_text)
        session.add(participant)
        await session.commit()
        await session.refresh(participant)
        return participant


async def is_raffle_participant(raffle_id: int, user_id: int) -> bool:
    async with async_session() as session:
        result = await session.execute(
            select(RaffleParticipant).where(
                RaffleParticipant.raffle_id == raffle_id, RaffleParticipant.user_id == user_id
            )
        )
        return result.scalar_one_or_none() is not None


async def count_participants(raffle_id: int) -> int:
    async with async_session() as session:
        result = await session.execute(
            select(func.count())
            .select_from(RaffleParticipant)
            .where(RaffleParticipant.raffle_id == raffle_id)
        )
        return result.scalar_one()


async def get_participants(raffle_id: int) -> list[RaffleParticipant]:
    async with async_session() as session:
        result = await session.execute(
            select(RaffleParticipant).where(RaffleParticipant.raffle_id == raffle_id)
        )
        return list(result.scalars().all())


async def count_all_raffles() -> int:
    async with async_session() as session:
        result = await session.execute(select(func.count()).select_from(Raffle))
        return result.scalar_one()


async def get_raffle_neighbors(current_number: int) -> tuple[int | None, int | None]:
    """Returns (previous_number, next_number) relative to current, ordered by number."""
    async with async_session() as session:
        prev_result = await session.execute(
            select(func.max(Raffle.number)).where(Raffle.number < current_number)
        )
        next_result = await session.execute(
            select(func.min(Raffle.number)).where(Raffle.number > current_number)
        )
        return prev_result.scalar_one(), next_result.scalar_one()


async def set_active_winners(raffle_id: int, winner_ids: list[int]) -> None:
    async with async_session() as session:
        await session.execute(
            update(RaffleParticipant)
            .where(RaffleParticipant.raffle_id == raffle_id, RaffleParticipant.user_id.in_(winner_ids))
            .values(is_winner=True)
        )
        await session.commit()


# -------------------------------------------------------------- actual info --
async def get_actual_info() -> str:
    async with async_session() as session:
        result = await session.execute(select(ActualInfo).order_by(ActualInfo.id.desc()).limit(1))
        row = result.scalar_one_or_none()
        return row.text if row else "Пока здесь пусто."


async def set_actual_info(text: str) -> None:
    async with async_session() as session:
        info = ActualInfo(text=text, updated_at=dt.datetime.utcnow())
        session.add(info)
        await session.commit()


# ----------------------------------------------------------------- broadcast --
async def log_broadcast(recipients_count: int) -> None:
    async with async_session() as session:
        log = BroadcastLog(recipients_count=recipients_count, sent_at=dt.datetime.utcnow())
        session.add(log)
        await session.commit()


async def get_last_broadcast_count() -> int:
    async with async_session() as session:
        result = await session.execute(select(BroadcastLog).order_by(BroadcastLog.id.desc()).limit(1))
        row = result.scalar_one_or_none()
        return row.recipients_count if row else 0


# ------------------------------------------------------------- last screen --
async def update_last_shown(
    user_id: int,
    message_id: int | None,
    image_id: str | None,
    extra_message_id: int | None = None,
) -> None:
    async with async_session() as session:
        await session.execute(
            update(User)
            .where(User.id == user_id)
            .values(last_message_id=message_id, last_image_id=image_id, last_extra_message_id=extra_message_id)
        )
        await session.commit()


# --------------------------------------------------------------- images ----
async def add_image(file_id: str, media_type: str = "photo") -> bool:
    """Returns False if this file_id is already in the library (duplicate)."""
    async with async_session() as session:
        exists = await session.execute(select(ImageLibrary).where(ImageLibrary.file_id == file_id))
        if exists.scalar_one_or_none():
            return False
        session.add(ImageLibrary(file_id=file_id, media_type=media_type))
        await session.commit()
        return True


async def count_images(media_type: str | None = None) -> int:
    async with async_session() as session:
        query = select(func.count()).select_from(ImageLibrary)
        if media_type:
            query = query.where(ImageLibrary.media_type == media_type)
        result = await session.execute(query)
        return result.scalar_one()


async def get_random_image(exclude: str | None = None) -> tuple[str, str] | None:
    """Returns (file_id, media_type) — may be a photo or a sticker — or None if the library is empty."""
    import random

    async with async_session() as session:
        result = await session.execute(select(ImageLibrary.file_id, ImageLibrary.media_type))
        all_items = list(result.all())

    if not all_items:
        return None
    if exclude and len(all_items) > 1:
        candidates = [item for item in all_items if item[0] != exclude]
        chosen = random.choice(candidates) if candidates else all_items[0]
    else:
        chosen = random.choice(all_items)
    return chosen[0], chosen[1]


async def list_images(limit: int = 10, offset: int = 0) -> list[ImageLibrary]:
    async with async_session() as session:
        result = await session.execute(
            select(ImageLibrary).order_by(ImageLibrary.id.desc()).limit(limit).offset(offset)
        )
        return list(result.scalars().all())


async def delete_image(image_id: int) -> bool:
    async with async_session() as session:
        item = await session.get(ImageLibrary, image_id)
        if item is None:
            return False
        await session.delete(item)
        await session.commit()
        return True
