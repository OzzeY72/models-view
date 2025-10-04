from aiogram import Router, F
from aiogram.types import CallbackQuery, InputMediaPhoto, FSInputFile
import requests
from dotenv import load_dotenv
import os
from utils import format_master, get_masters_keyboard, preload_image

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
API_URL = os.getenv("API_URL")

router = Router()
models_cache = []

# def get_master_keyboard(current: int, total: int, master_id: str) -> InlineKeyboardMarkup:
#   return InlineKeyboardMarkup(
#     inline_keyboard=[
#       [
#         InlineKeyboardButton(text="⬅️", callback_data=f"prev_models:{current}"),
#         InlineKeyboardButton(text=f"{current+1}/{total}", callback_data="noop"),
#         InlineKeyboardButton(text="➡️", callback_data=f"next_models:{current}")
#       ],
#       [
#           InlineKeyboardButton(text="Menu", callback_data="go_home")
#       ]
#     ]
#   )

@router.callback_query(F.data.startswith("show_models"))
async def list_models(callback: CallbackQuery):
    print("SHOW MODELS")
    _, category = callback.data.split(":")
    url = f"{API_URL}/{'top' if category == 'top' else 'regular'}/"

    resp = requests.get(url)
    resp.raise_for_status()
    global models_cache
    models_cache = resp.json()

    if not models_cache:
        await callback.message.answer("📭 No models found")
        await callback.answer()
        return

    current = 0
    m = models_cache[current]

    text = format_master(m)
    kb = get_masters_keyboard(current, len(models_cache), m.get("id"), prev_name="prev_models", next_name="next_models")

    if m.get("photos"):
        photo = await preload_image(m, API_URL)
        await callback.message.answer_photo(photo, caption=text, reply_markup=kb)
    else:
        await callback.message.answer(text, reply_markup=kb)

    await callback.answer()

@router.callback_query(F.data.startswith("prev_models"))
async def prev_master(callback: CallbackQuery):
    _, current = callback.data.split(":")
    current = int(current)
    total = len(models_cache)

    new_index = (current - 1) % total
    m = models_cache[new_index]
    text = format_master(m)
    kb = get_masters_keyboard(new_index, total, m.get("id"), prev_name="prev_models", next_name="next_models")

    await update_master_message(callback, m, text, kb, new_index)

# Перелистывание вперёд
@router.callback_query(F.data.startswith("next_models"))
async def next_master(callback: CallbackQuery):
    _, current = callback.data.split(":")
    current = int(current)
    total = len(models_cache)

    new_index = (current + 1) % total
    m = models_cache[new_index]
    text = format_master(m)
    kb = get_masters_keyboard(new_index, total, m.get("id"), prev_name="prev_models", next_name="next_models")

    await update_master_message(callback, m, text, kb, new_index)

async def update_master_message(callback: CallbackQuery, m, text, kb, new_index):
    if m.get("photos"):
      photo = await preload_image(m, API_URL)
      media = InputMediaPhoto(media=photo, caption=text)
      await callback.message.edit_media(media=media, reply_markup=kb)
    else:
      try:
        await callback.message.edit_caption(caption=text, reply_markup=kb)
      except:
        await callback.message.edit_text(text, reply_markup=kb)

    await callback.answer()

@router.callback_query(F.data == "noop")
async def noop(callback: CallbackQuery):
    await callback.answer()
