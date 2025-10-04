import os
from dotenv import load_dotenv
from aiogram import Router, F
from aiogram import Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
API_URL = os.getenv("API_URL")

router = Router()

@router.callback_query(F.data == "work")
async def work_with_us(callback: CallbackQuery):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Work with us",
                    web_app=WebAppInfo(url=f"{API_URL}/static/miniapp/index.html")
                )
            ]
        ]
    )
    await callback.message.answer("Sign up:", reply_markup=keyboard)
