from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command

import tempfile

router = Router()

# --- Главное меню ---
menu = ReplyKeyboardMarkup(
  keyboard=[
    [KeyboardButton(text="📋 List models")],
  ],
  resize_keyboard=True
)

@router.message(Command("start"))
async def start(message: Message):
  await message.answer("Hi 👋 Wanna watch catalogue ?", reply_markup=menu)