import glob
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import os
from aiogram import Router, F
from aiogram.types import CallbackQuery, InputMediaPhoto, FSInputFile
from aiogram.fsm.context import FSMContext
from handlers.list_model import get_master_keyboard
from states import SearchMasters
from utils import format_master, get_masters_keyboard, preload_image, send_master_carousel
from dotenv import load_dotenv
from aiogram.types import Message
import requests

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
API_URL = os.getenv("API_URL")

router = Router()
models_cache = []

SEARCH_PARAMS = [
    "age", "city", "height", "weight", "cupsize", 
    "clothsize", "price_1h", "price_full_day"
]

def get_search_keyboard(current_params: dict):
    """
    current_params: словарь выбранных фильтров
    """
    buttons = []

    # создаём кнопки параметров
    SEARCH_PARAMS = [
        "age", "city", "height", "weight", "cupsize",
        "clothsize", "price_1h", "price_full_day"
    ]

    row = []
    for param in SEARCH_PARAMS:
        text = param
        if param in current_params:
            text += f" ✅ {current_params[param]}"
        row.append(InlineKeyboardButton(text=text, callback_data=f"search_set:{param}"))

        # добавляем по 2 кнопки в ряд
        if len(row) == 2:
            buttons.append(row)
            row = []

    # если осталась кнопка без пары
    if row:
        buttons.append(row)

    # кнопка выполнить поиск
    buttons.append([InlineKeyboardButton(text="🔍 Search", callback_data="search_execute")])

    # создаём InlineKeyboardMarkup с готовым массивом кнопок
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    return kb

@router.callback_query(F.data == "search_post")
async def search_post_callback(callback: CallbackQuery, state: FSMContext):
    """
    Показывает пост с текущими фильтрами и кнопками установки параметров
    """
    await state.clear()
    params = await state.get_data() 
    if not params:
        params = {}

    text_lines = ["🔎 Search models by parameters:"]
    if params:
        for k, v in params.items():
            text_lines.append(f"{k}: {v}")

    text = "\n".join(text_lines)
    kb = get_search_keyboard(params)
    await callback.message.answer(text, reply_markup=kb)
    await callback.answer()

@router.callback_query(F.data.startswith("search_set:"))
async def search_set_param(callback: CallbackQuery, state: FSMContext):
    _, param = callback.data.split(":")
    await state.update_data(current_param=param)
    await state.set_state(SearchMasters.entering_value)
    await callback.message.answer(f"Enter value for {param}:")
    await callback.answer()

@router.message(SearchMasters.entering_value)
async def enter_param_value(message: Message, state: FSMContext):
    data = await state.get_data()
    param = data["current_param"]

    # сохраняем введённое значение
    await state.update_data({param: message.text})
    await state.set_state(SearchMasters.selecting_param)

    # показываем пост поиска снова с обновлёнными фильтрами
    params = await state.get_data()
    kb = get_search_keyboard(params)
    text_lines = ["🔎 Search models by parameters:"]
    for k, v in params.items():
        if k != "current_param":
            text_lines.append(f"{k}: {v}")
    text = "\n".join(text_lines)
    await message.answer(text, reply_markup=kb)

@router.callback_query(F.data == "search_execute")
async def search_execute(callback: CallbackQuery, state: FSMContext):
    params = await state.get_data()

    # убираем служебный ключ
    params.pop("current_param", None)

    # делаем запрос на бекенд с параметрами
    resp = requests.get(f"{API_URL}/masters/search", params=params)
    resp.raise_for_status()
    masters = resp.json()
    global models_cache
    models_cache = masters
    
    if not masters:
        await callback.message.answer("📭 No models found with selected parameters.")
        await state.clear()
        return

    # сохраняем кэш для карусели
    await state.update_data(search_results=masters)
    await send_master_carousel(callback.message, masters, state, index=0, 
                               prev_name="prev_search", next_name="next_search")
    await callback.answer()

@router.callback_query(F.data.startswith("prev_search"))
async def prev_master(callback: CallbackQuery):
    _, current = callback.data.split(":")
    current = int(current)
    total = len(models_cache)

    new_index = (current - 1) % total
    m = models_cache[new_index]
    text = format_master(m)

    kb = get_masters_keyboard(new_index, total, m.get("id"), "prev_search", "next_search")

    await update_master_message(callback, m, text, kb, new_index)

# Перелистывание вперёд
@router.callback_query(F.data.startswith("next_search"))
async def next_master(callback: CallbackQuery):
    _, current = callback.data.split(":")
    current = int(current)
    total = len(models_cache)

    new_index = (current + 1) % total
    m = models_cache[new_index]
    text = format_master(m)
    
    kb = get_masters_keyboard(new_index, total, m.get("id"), "prev_search", "next_search")

    await update_master_message(callback, m, text, kb, new_index)

async def update_master_message(callback: CallbackQuery, m, text, kb, new_index):
    if m.get("main_photo"):
      photo = await preload_image(m, API_URL)
      media = InputMediaPhoto(media=photo, caption=text)
      await callback.message.edit_media(media=media, reply_markup=kb)
    else:
      try:
        await callback.message.edit_caption(caption=text, reply_markup=kb)
      except:
        await callback.message.edit_text(text, reply_markup=kb)

    await callback.answer()


# async def send_master_carousel(message, masters, state, index=0):
#     m = masters[index]
#     text = format_master(m)
    
#     kb = InlineKeyboardMarkup(inline_keyboard=[
#         [
#             InlineKeyboardButton(text="⬅️", callback_data=f"search_prev:{index}"),
#             InlineKeyboardButton(text=f"{index+1}/{len(masters)}", callback_data="noop"),
#             InlineKeyboardButton(text="➡️", callback_data=f"search_next:{index}")
#         ],
#         [
#             InlineKeyboardButton(text="Menu", callback_data="go_home")
#         ]
#     ])

#     if m.get("main_photo"):
#         photo = await preload_image(m, API_URL)
#         await message.answer_photo(photo, caption=text, reply_markup=kb)
#     else:
#         await message.answer(text, reply_markup=kb)

# @router.callback_query(F.data.startswith("search_prev"))
# async def search_prev(callback: CallbackQuery, state: FSMContext):
#     _, current = callback.data.split(":")
#     current = int(current)
#     data = await state.get_data()
#     masters = data["search_results"]
#     new_index = (current - 1) % len(masters)
#     await send_master_carousel(callback.message, masters, state, new_index)
#     await callback.answer()

# @router.callback_query(F.data.startswith("search_next"))
# async def search_next(callback: CallbackQuery, state: FSMContext):
#     _, current = callback.data.split(":")
#     current = int(current)
#     data = await state.get_data()
#     masters = data["search_results"]
#     new_index = (current + 1) % len(masters)
#     await send_master_carousel(callback.message, masters, state, new_index)
#     await callback.answer()