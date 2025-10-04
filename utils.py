import requests, tempfile
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo, FSInputFile
from dotenv import load_dotenv
import os

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
API_URL = os.getenv("API_URL")
API_URL_HTTPS = os.getenv("API_URL_HTTPS")

def format_master(m: dict) -> str:
  return (
    f"👩 <b>{m['name']}</b>, {m['age']} y.o.\n\n"
    f"📞 Phone: {m['phonenumber']}\n"
    f"🏠 Address: {m['address']}\n\n"
    f"📐 Parameters:\n"
    f"   Height: {m['height']} cm | Weight: {m['weight']} kg\n"
    f"   Cup: {m['cupsize']} | Body type: {m['bodytype']}\n\n"
    f"💰 Prices:\n"
    f"   1 hour: {m['price_1h']} $\n"
    f"   2 hours: {m['price_2h']} $\n"
    f"   Full day: {m['price_full_day']} $\n\n"
    f"📲 Call: {m['phonenumber']}"
  )

def format_agencyspa(a: dict) -> str:
  return (
    f"🏢 <b>{a.get('name')}</b>\n"
    f"📍 Address: {a.get('address', 'N/A')}\n"
    f"📞 Phone: {a.get('phone', 'N/A')}\n"
  )

def get_masters_keyboard(index: int, total: int, master_id: str, prev_name, next_name) -> InlineKeyboardMarkup:
  return InlineKeyboardMarkup(inline_keyboard=[
      [InlineKeyboardButton(
          text="📷 Show Photos",
          web_app=WebAppInfo(url=f"{API_URL_HTTPS}/masters_view/{master_id}")
      )],
      [
          InlineKeyboardButton(text="⬅️", callback_data=f"{prev_name}:{index}"),
          InlineKeyboardButton(text=f"{index+1}/{total}", callback_data="noop"),
          InlineKeyboardButton(text="➡️", callback_data=f"{next_name}:{index}")
      ],
      [
          InlineKeyboardButton(text="Menu", callback_data="go_home")
      ]
  ])

async def send_master_carousel(message, masters, state, index=0, prev_name="prev", next_name="next"):
    m = masters[index]
    text = format_master(m)
    
    kb = get_masters_keyboard(index, len(masters), m.get("id"), prev_name, next_name)

    if m.get("photos"):
        photo = await preload_image(m, API_URL)
        await message.answer_photo(photo, caption=text, reply_markup=kb)
    else:
        await message.answer(text, reply_markup=kb)

async def preload_image(m, API_URL) :
  if m.get("photos"):
    try:
      photo_resp = requests.get(f"{API_URL}/static/{m['photos'][0]}", stream=True)
      photo_resp.raise_for_status()

      if "image" not in photo_resp.headers.get("content-type", ""):
        print(f"⚠️ Not an image URL")

      with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
        for chunk in photo_resp.iter_content(1024):
          tmp.write(chunk)
        tmp_path = tmp.name

      photo = FSInputFile(tmp_path)
      return photo

    except Exception as e:
      print(f"⚠️ Could not load photo: {e}")