from aiogram.fsm.state import State, StatesGroup


class SuggestStates(StatesGroup):
    choosing_mode = State()      # anonymous / public
    waiting_media = State()
    waiting_description = State()
    preview = State()


class RaffleCreateStates(StatesGroup):
    number = State()
    title = State()
    description = State()
    winners_count = State()
    hours = State()
    preview = State()


class RaffleEditStates(StatesGroup):
    choosing_field = State()
    waiting_value = State()


class RaffleJoinStates(StatesGroup):
    waiting_proof = State()


class ActualEditStates(StatesGroup):
    waiting_text = State()


class NotSendStates(StatesGroup):
    waiting_content = State()


class ModerationCommentStates(StatesGroup):
    waiting_comment = State()
