from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from config import settings
from database.requests import add_image, count_images
from utils.states import ImageLibraryStates

router = Router(name="admin_images")


def _admin_only(message: Message) -> bool:
    return message.from_user.id in settings.admin_ids


@router.message(Command("addimage"))
async def cmd_addimage(message: Message, state: FSMContext) -> None:
    if not _admin_only(message):
        return
    await state.set_state(ImageLibraryStates.collecting)
    current = await count_images()
    await message.answer(
        "📸 Пришли одно или несколько квадратных фото подряд — каждое добавится в библиотеку.\n"
        f"Сейчас в библиотеке: {current}.\n\n"
        "Когда закончишь — отправь /done."
    )


@router.message(Command("done"))
async def cmd_done(message: Message, state: FSMContext) -> None:
    if not _admin_only(message):
        return
    if await state.get_state() == ImageLibraryStates.collecting.state:
        await state.clear()
        total = await count_images()
        await message.answer(f"✅ Готово. Всего изображений в библиотеке: {total}.")


@router.message(ImageLibraryStates.collecting, F.photo)
async def collect_photo(message: Message) -> None:
    file_id = message.photo[-1].file_id
    added = await add_image(file_id)
    total = await count_images()
    if added:
        await message.answer(f"✅ Добавлено. Всего: {total}. Присылай еще или отправь /done.")
    else:
        await message.answer("⚠️ Это фото уже есть в библиотеке. Присылай еще или отправь /done.")


@router.message(Command("imagescount"))
async def cmd_imagescount(message: Message) -> None:
    if not _admin_only(message):
        return
    total = await count_images()
    await message.answer(f"📸 В библиотеке {total} изображений.")
