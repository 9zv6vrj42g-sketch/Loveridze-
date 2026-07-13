from aiogram import F, Router
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from config import settings
from database.requests import add_image, count_images, delete_image, list_images
from utils.states import ImageLibraryStates

router = Router(name="admin_images")

PAGE_SIZE = 10


def _admin_only(message_or_callback) -> bool:
    return message_or_callback.from_user.id in settings.admin_ids


# --------------------------------------------------------------- /addimage --
@router.message(Command("addimage"))
async def cmd_addimage(message: Message, state: FSMContext) -> None:
    if not _admin_only(message):
        return
    await state.set_state(ImageLibraryStates.collecting)
    await state.update_data(media_type="photo")
    current = await count_images("photo")
    await message.answer(
        "📸 Пришли одно или несколько квадратных фото подряд — каждое добавится в библиотеку.\n"
        f"Сейчас фото в библиотеке: {current}.\n\n"
        "Когда закончишь — отправь /done."
    )


# -------------------------------------------------------------- /addsticker --
@router.message(Command("addsticker"))
async def cmd_addsticker(message: Message, state: FSMContext) -> None:
    if not _admin_only(message):
        return
    await state.set_state(ImageLibraryStates.collecting)
    await state.update_data(media_type="sticker")
    current = await count_images("sticker")
    await message.answer(
        "🎭 Пришли один или несколько стикеров подряд (можно из набора Lavrelin) — каждый добавится в библиотеку.\n"
        f"Сейчас стикеров в библиотеке: {current}.\n\n"
        "Когда закончишь — отправь /done."
    )


@router.message(Command("done"))
async def cmd_done(message: Message, state: FSMContext) -> None:
    if not _admin_only(message):
        return
    if await state.get_state() == ImageLibraryStates.collecting.state:
        await state.clear()
        photos = await count_images("photo")
        stickers = await count_images("sticker")
        await message.answer(f"✅ Готово. В библиотеке: {photos} фото, {stickers} стикеров.")


@router.message(ImageLibraryStates.collecting, F.photo)
async def collect_photo(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    if data.get("media_type") != "photo":
        await message.answer("Сейчас идет добавление стикеров. Пришли стикер или отправь /done.")
        return
    file_id = message.photo[-1].file_id
    added = await add_image(file_id, media_type="photo")
    total = await count_images("photo")
    if added:
        await message.answer(f"✅ Добавлено. Всего фото: {total}. Присылай еще или отправь /done.")
    else:
        await message.answer("⚠️ Это фото уже есть в библиотеке. Присылай еще или отправь /done.")


@router.message(ImageLibraryStates.collecting, F.sticker)
async def collect_sticker(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    if data.get("media_type") != "sticker":
        await message.answer("Сейчас идет добавление фото. Пришли фото или отправь /done.")
        return
    file_id = message.sticker.file_id
    added = await add_image(file_id, media_type="sticker")
    total = await count_images("sticker")
    if added:
        await message.answer(f"✅ Добавлено. Всего стикеров: {total}. Присылай еще или отправь /done.")
    else:
        await message.answer("⚠️ Этот стикер уже есть в библиотеке. Присылай еще или отправь /done.")


@router.message(Command("imagescount"))
async def cmd_imagescount(message: Message) -> None:
    if not _admin_only(message):
        return
    photos = await count_images("photo")
    stickers = await count_images("sticker")
    await message.answer(f"📸 Фото в библиотеке: {photos}\n🎭 Стикеров в библиотеке: {stickers}")


# ------------------------------------------------------------- /imagedelete --
def _delete_list_kb(items, offset: int, has_more: bool) -> InlineKeyboardMarkup:
    rows = []
    for item in items:
        icon = "📸" if item.media_type == "photo" else "🎭"
        rows.append(
            [InlineKeyboardButton(text=f"🗑 #{item.id} {icon}", callback_data=f"imgdel:{item.id}:{offset}")]
        )
    nav = []
    if offset > 0:
        nav.append(InlineKeyboardButton(text="👈", callback_data=f"imgdel_page:{max(offset - PAGE_SIZE, 0)}"))
    if has_more:
        nav.append(InlineKeyboardButton(text="👉", callback_data=f"imgdel_page:{offset + PAGE_SIZE}"))
    if nav:
        rows.append(nav)
    rows.append([InlineKeyboardButton(text="✖️ Закрыть", callback_data="imgdel_close")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


async def _render_delete_list(offset: int):
    items = await list_images(limit=PAGE_SIZE + 1, offset=offset)
    has_more = len(items) > PAGE_SIZE
    items = items[:PAGE_SIZE]
    if not items:
        return "Библиотека пуста.", None
    text = "🗑 Выбери, что удалить:\n\n" + "\n".join(
        f"#{item.id} — {'📸 фото' if item.media_type == 'photo' else '🎭 стикер'}" for item in items
    )
    return text, _delete_list_kb(items, offset, has_more)


@router.message(Command("imagedelete"))
async def cmd_imagedelete(message: Message) -> None:
    if not _admin_only(message):
        return
    text, kb = await _render_delete_list(0)
    await message.answer(text, reply_markup=kb)


@router.callback_query(F.data.startswith("imgdel_page:"))
async def imgdel_page(callback: CallbackQuery) -> None:
    if not _admin_only(callback):
        await callback.answer("Только для администрации", show_alert=True)
        return
    offset = int(callback.data.split(":")[-1])
    text, kb = await _render_delete_list(offset)
    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data.startswith("imgdel:"))
async def imgdel_confirm(callback: CallbackQuery) -> None:
    if not _admin_only(callback):
        await callback.answer("Только для администрации", show_alert=True)
        return
    _, image_id_str, offset_str = callback.data.split(":")
    ok = await delete_image(int(image_id_str))
    text, kb = await _render_delete_list(int(offset_str))
    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer("Удалено ✅" if ok else "Уже удалено")


@router.callback_query(F.data == "imgdel_close")
async def imgdel_close(callback: CallbackQuery) -> None:
    await callback.message.delete()
    await callback.answer()
