from __future__ import annotations

import datetime as dt

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)  # telegram user id
    username: Mapped[str | None] = mapped_column(String(64), nullable=True)
    full_name: Mapped[str | None] = mapped_column(String(256), nullable=True)
    notifications_on: Mapped[bool] = mapped_column(Boolean, default=True)
    is_banned: Mapped[bool] = mapped_column(Boolean, default=False)
    ban_comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    muted_until: Mapped[dt.datetime | None] = mapped_column(DateTime, nullable=True)
    mute_comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_suggestion_at: Mapped[dt.datetime | None] = mapped_column(DateTime, nullable=True)
    joined_at: Mapped[dt.datetime] = mapped_column(DateTime, default=dt.datetime.utcnow)
    last_message_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    last_image_id: Mapped[str | None] = mapped_column(String(256), nullable=True)
    last_extra_message_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)


class Suggestion(Base):
    __tablename__ = "suggestions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger)
    is_anonymous: Mapped[bool] = mapped_column(Boolean, default=False)
    media_type: Mapped[str | None] = mapped_column(String(32), nullable=True)  # photo/video/document
    media_file_id: Mapped[str | None] = mapped_column(String(256), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=dt.datetime.utcnow)
    mod_chat_message_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)


class Raffle(Base):
    __tablename__ = "raffles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    number: Mapped[int] = mapped_column(Integer, unique=True)
    title: Mapped[str] = mapped_column(String(256))
    description: Mapped[str] = mapped_column(Text)
    winners_count: Mapped[int] = mapped_column(Integer)
    duration_hours: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(16), default="inactive")  # inactive/active/finished
    started_at: Mapped[dt.datetime | None] = mapped_column(DateTime, nullable=True)
    ends_at: Mapped[dt.datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=dt.datetime.utcnow)
    result_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    participants: Mapped[list["RaffleParticipant"]] = relationship(
        back_populates="raffle", cascade="all, delete-orphan"
    )


class RaffleParticipant(Base):
    __tablename__ = "raffle_participants"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    raffle_id: Mapped[int] = mapped_column(ForeignKey("raffles.id"))
    user_id: Mapped[int] = mapped_column(BigInteger)
    proof_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    joined_at: Mapped[dt.datetime] = mapped_column(DateTime, default=dt.datetime.utcnow)
    is_winner: Mapped[bool] = mapped_column(Boolean, default=False)

    raffle: Mapped["Raffle"] = relationship(back_populates="participants")


class ActualInfo(Base):
    """Singleton-style table: the current '❗️Актуальное' description."""

    __tablename__ = "actual_info"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    text: Mapped[str] = mapped_column(Text, default="Пока здесь пусто.")
    updated_at: Mapped[dt.datetime] = mapped_column(DateTime, default=dt.datetime.utcnow)


class BroadcastLog(Base):
    """Tracks how many users received the last /notsend broadcast."""

    __tablename__ = "broadcast_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    recipients_count: Mapped[int] = mapped_column(Integer, default=0)
    sent_at: Mapped[dt.datetime] = mapped_column(DateTime, default=dt.datetime.utcnow)


class ImageLibrary(Base):
    """Square photos AND stickers (by Telegram file_id) used as the backdrop for every screen."""

    __tablename__ = "image_library"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    file_id: Mapped[str] = mapped_column(String(256), unique=True)
    media_type: Mapped[str] = mapped_column(String(16), default="photo")  # "photo" or "sticker"
    added_at: Mapped[dt.datetime] = mapped_column(DateTime, default=dt.datetime.utcnow)
