import os
import asyncio
import requests
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher,F
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage

from handlers.list_model import router as list_masters_router
from handlers.list_agencies import router as list_agencies_router
from handlers.search import router as search_router
from handlers.application import router as application_router
from handlers.start import router as start_router

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(
  token=BOT_TOKEN,
  default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher(storage=MemoryStorage())
dp.include_router(start_router)
dp.include_router(list_masters_router)
dp.include_router(list_agencies_router)
dp.include_router(search_router)
dp.include_router(application_router)

if __name__ == "__main__":
  asyncio.run(dp.start_polling(bot))
