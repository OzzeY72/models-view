from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import os
from aiogram import Router, F
from aiogram.types import CallbackQuery, InputMediaPhoto, FSInputFile
from aiogram.fsm.context import FSMContext
from states import SearchMasters
from utils import format_master, get_masters_keyboard, preload_image, send_master_carousel
from dotenv import load_dotenv
import requests
from pathlib import Path

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
API_URL = os.getenv("API_URL")

router = Router()
models_cache = []

SEARCH_PARAMS = [
    "age", "height", "cupsize", "bodytype"
]

async def update_search_post(message, state: FSMContext):
    params = await state.get_data()
    params.pop("search_results", None)

    text_lines = ["🔎 Search models by parameters:"]
    if params:
        for k, v in params.items():
            if k != "current_param":
                if "_" in v:
                    v = v.replace("_", "&lt;")
                text_lines.append(f"{k}: {v}")

    text = "\n".join(text_lines)
    kb = get_search_keyboard(params)

    photo_path = CURRENT_DIR / ".." / "static" / "search_post.webp"
    photo = FSInputFile(photo_path.resolve())

    try:
        await message.edit_media(
            media=InputMediaPhoto(media=photo, caption=text),
            reply_markup=kb
        )
    except Exception:
        await message.edit_caption(caption=text, reply_markup=kb)


def get_search_keyboard(current_params: dict):
    """
    current_params: словарь выбранных фильтров
    """
    buttons = []

    row = []
    for param in SEARCH_PARAMS:
        text = param
        if param in current_params:
            val = current_params[param]
            if "_" in val:
                val = val.replace("_", "<")
            text += f" ✅ {val}"
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

CURRENT_DIR = Path(__file__).parent

@router.callback_query(F.data == "search_post")
async def search_post_callback(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await update_search_post(callback.message, state)
    await callback.answer()

@router.callback_query(F.data.startswith("search_set:"))
async def search_set_param(callback: CallbackQuery, state: FSMContext):
    _, param = callback.data.split(":")
    await state.set_state(SearchMasters.entering_value)

    match param:
        case "age":
            kb = get_age_keyboard()
            title = "Select age range:"
        case "height":
            kb = get_height_keyboard()
            title = "Select height range:"
        case "cupsize":
            kb = get_cupsize_keyboard()
            title = "Select cup size:"
        case "bodytype":
            kb = get_bodytype_keyboard()
            title = "Select body type:"

    try:
        await callback.message.edit_caption(caption=title, reply_markup=kb)
    except:
        await callback.message.edit_text(text=title, reply_markup=kb)

    await callback.answer()

@router.callback_query(F.data.startswith("search_enter:"))
async def enter_param_value(callback: CallbackQuery, state: FSMContext):
    _, param, data = callback.data.split(":")
    await state.update_data({param: data})
    await state.set_state(SearchMasters.selecting_param)
    await update_search_post(callback.message, state)
    await callback.answer()

@router.callback_query(F.data == "search_execute")
async def search_execute(callback: CallbackQuery, state: FSMContext):
    params = await state.get_data()
    params.pop("current_param", None)

    new_params = {}
    for param, data in params.items():  
        if "cm" in data:
            data = data.replace("cm", "")

        if "-" in data:
            v1, v2 = data.split("-")
            new_params[f"{param}_from"] = v1
            new_params[f"{param}_to"]   = v2
        elif "_" in data:
            v = data.replace("_", "")
            new_params[f"{param}_to"] = v
        elif "+" in data:
            v = data.replace("+", "")
            new_params[f"{param}_from"] = v
        else:
            if data != "All":
                new_params[param] = data

    print(f"{API_URL}/masters/search")
    resp = requests.get(f"{API_URL}/masters/search", params=new_params)
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

def get_age_keyboard():
    buttons = [
        [InlineKeyboardButton(text="18-25", callback_data="search_enter:age:18-25"),
         InlineKeyboardButton(text="26-30", callback_data="search_enter:age:26-30")],
        [InlineKeyboardButton(text="31+", callback_data="search_enter:age:31+"),
        InlineKeyboardButton(text="All", callback_data="search_enter:age:All")],
        [InlineKeyboardButton(text="Back to Search", callback_data="search_post")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_height_keyboard():
    buttons = [
        [InlineKeyboardButton(text="<160 cm", callback_data="search_enter:height:_160cm"),
         InlineKeyboardButton(text="160-170 cm", callback_data="search_enter:height:160cm-170cm")],
        [InlineKeyboardButton(text="170+ cm", callback_data="search_enter:height:170+cm"),
         InlineKeyboardButton(text="All", callback_data="search_enter:height:All")],
        [InlineKeyboardButton(text="Back to Search", callback_data="search_post")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_cupsize_keyboard():
    buttons = [
        [InlineKeyboardButton(text="1", callback_data="search_enter:cupsize:1"),
         InlineKeyboardButton(text="2", callback_data="search_enter:cupsize:2")],
        [InlineKeyboardButton(text="3", callback_data="search_enter:cupsize:3"),
         InlineKeyboardButton(text="4+", callback_data="search_enter:cupsize:4+")],
        [InlineKeyboardButton(text="All", callback_data="search_enter:cupsize:All")],
        [InlineKeyboardButton(text="Back to Search", callback_data="search_post")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_bodytype_keyboard():
    buttons = [
        [InlineKeyboardButton(text="Skinny", callback_data="search_enter:bodytype:Skinny"),
            InlineKeyboardButton(text="Slim", callback_data="search_enter:bodytype:Slim"),
        ],
        [InlineKeyboardButton(text="Athletic", callback_data="search_enter:bodytype:Athletic"),
            InlineKeyboardButton(text="Curvy", callback_data="search_enter:bodytype:Curvy")],
        [InlineKeyboardButton(text="All", callback_data="search_enter:bodytype:All")],
        [InlineKeyboardButton(text="Back to Search", callback_data="search_post")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


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