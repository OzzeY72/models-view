from aiogram import Router, F, Bot
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from handlers.start import hello_message
from states import CreateAgencySpa, CreateApplication
import os, tempfile, requests
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.types import CallbackQuery
from dotenv import load_dotenv

load_dotenv()
API_URL = os.getenv("API_URL")
API_KEY = os.getenv("API_KEY")
headers = {"X-API-Key": API_KEY}

router = Router()

async def work_with_us(message: Message, state: FSMContext):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👩 Model", callback_data="apply_model")],
        [InlineKeyboardButton(text="🏢 Agency", callback_data="apply_agency")],
        [InlineKeyboardButton(text="🏖️ SPA", callback_data="apply_spa")],
    ])
    await message.answer("Choose application type:", reply_markup=kb)

@router.callback_query(F.data.startswith("work"))
async def start_create_applications(callback: CallbackQuery, state: FSMContext):
    await work_with_us(callback.message, state)
    await callback.answer()

@router.callback_query(F.data == "apply_agency")
async def apply_agency(callback: CallbackQuery, state: FSMContext):
    # тут новый FSM для AgencyApplication
    await state.set_state(CreateAgencySpa.name)
    await callback.message.answer("Enter agency name:")
    await state.update_data(is_agency=True)
    await callback.answer()

@router.callback_query(F.data == "apply_spa")
async def apply_spa(callback: CallbackQuery, state: FSMContext):
    # FSM для SPA, но логика такая же, только is_agency=False
    await state.set_state(CreateAgencySpa.name)
    await callback.message.answer("Enter SPA name:")
    await state.update_data(is_agency=False)
    await callback.answer()

@router.message(CreateAgencySpa.name)
async def process_agency_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(CreateAgencySpa.phone)
    await message.answer("Enter phone:")

@router.message(CreateAgencySpa.phone)
async def process_agency_phone(message: Message, state: FSMContext):
    await state.update_data(phone=message.text)
    await state.set_state(CreateAgencySpa.address)
    await message.answer("Enter address:")

@router.message(CreateAgencySpa.address)
async def process_agency_address(message: Message, state: FSMContext):
    await state.update_data(address=message.text)
    await state.set_state(CreateAgencySpa.photos)
    await message.answer("Now send photo:")

@router.message(CreateAgencySpa.photos, F.content_type == "photo")
async def process_agency_photo(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    photo = message.photo[-1]

    # получаем файл с Telegram
    file = await bot.get_file(photo.file_id)
    tmp = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
    await bot.download_file(file.file_path, destination=tmp.name)
    tmp.close()

    # собираем payload и files для form-data
    payload = {
        "name": data["name"],
        "phone": data["phone"],
        "is_agency": data["is_agency"],
        "address": data.get("address", ""),
    }

    with open(tmp.name, "rb") as f:
        files = {"file": f}
        resp = requests.post(f"{API_URL}/agency_spa_applications/", data=payload, files=files, headers=headers)

    if resp.status_code in (200, 201):
        await hello_message(message)
        # await message.answer("✅ Application submitted successfully!")
    else:
        await message.answer(f"❌ Error submitting application: {resp.text}")

    os.remove(tmp.name)
    await state.clear()



# --- 1. Старт ---
@router.callback_query(F.data.startswith("apply_model"))
async def start_create_application(callback: CallbackQuery, state: FSMContext):
    await state.set_state(CreateApplication.name)
    await callback.message.answer("Enter your name:")

# --- 2. Имя ---
@router.message(CreateApplication.name)
async def process_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(CreateApplication.age)
    await message.answer("Enter age:")

# --- 3. Возраст ---
@router.message(CreateApplication.age)
async def process_age(message: Message, state: FSMContext):
    await state.update_data(age=int(message.text))
    await state.set_state(CreateApplication.phonenumber)
    await message.answer("Enter phone number:")

# --- 4. Телефон ---
@router.message(CreateApplication.phonenumber)
async def process_phone(message: Message, state: FSMContext):
    await state.update_data(phonenumber=message.text)
    await state.set_state(CreateApplication.address)
    await message.answer("Enter address:")

# --- 5. Адрес ---
@router.message(CreateApplication.address)
async def process_address(message: Message, state: FSMContext):
    await state.update_data(address=message.text)
    await state.set_state(CreateApplication.height)
    await message.answer("Enter height (cm):")

# --- 6. Рост ---
@router.message(CreateApplication.height)
async def process_height(message: Message, state: FSMContext):
    await state.update_data(height=float(message.text))
    await state.set_state(CreateApplication.weight)
    await message.answer("Enter weight (kg):")

# --- 7. Вес ---
@router.message(CreateApplication.weight)
async def process_weight(message: Message, state: FSMContext):
    await state.update_data(weight=float(message.text))
    await state.set_state(CreateApplication.cupsize)
    await message.answer("Enter cup size (number):")

# --- 8. Размер чашки ---
@router.message(CreateApplication.cupsize)
async def process_cupsize(message: Message, state: FSMContext):
    await state.update_data(cupsize=int(message.text))
    await state.set_state(CreateApplication.clothsize)
    await message.answer("Enter cloth size:")

# --- 9. Размер одежды ---
@router.message(CreateApplication.clothsize)
async def process_clothsize(message: Message, state: FSMContext):
    await state.update_data(clothsize=int(message.text))
    await state.set_state(CreateApplication.price_1h)
    await message.answer("Enter price for 1 hour:")

# --- 10. Цена 1ч ---
@router.message(CreateApplication.price_1h)
async def process_price_1h(message: Message, state: FSMContext):
    await state.update_data(price_1h=float(message.text))
    await state.set_state(CreateApplication.price_2h)
    await message.answer("Enter price for 2 hours:")

# --- 11. Цена 2ч ---
@router.message(CreateApplication.price_2h)
async def process_price_2h(message: Message, state: FSMContext):
    await state.update_data(price_2h=float(message.text))
    await state.set_state(CreateApplication.price_full_day)
    await message.answer("Enter price for full day:")

# --- 12. Цена день ---
@router.message(CreateApplication.price_full_day)
async def process_price_day(message: Message, state: FSMContext):
    await state.update_data(price_full_day=float(message.text))
    await state.set_state(CreateApplication.photo)
    await message.answer("Now send your main photo:")

@router.message(CreateApplication.photo, F.content_type == "photo")
async def process_photo(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    photo = message.photo[-1]

    # получаем файл с Telegram
    file = await bot.get_file(photo.file_id)
    tmp = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
    await bot.download_file(file.file_path, destination=tmp.name)
    tmp.close()

    # собираем payload и files для form-data
    payload = {
        "name": data["name"],
        "age": str(data["age"]),
        "phonenumber": data["phonenumber"],
        "address": data.get("address", ""),
        "height": str(data.get("height", "")),
        "weight": str(data.get("weight", "")),
        "cupsize": str(data.get("cupsize", "")),
        "clothsize": str(data.get("clothsize", "")),
        "price_1h": str(data.get("price_1h", "")),
        "price_2h": str(data.get("price_2h", "")),
        "price_full_day": str(data.get("price_full_day", "")),
        "is_top": str(False)
    }

    with open(tmp.name, "rb") as f:
        files = {"file": f}
        resp = requests.post(f"{API_URL}/applications", data=payload, files=files, headers=headers)

    if resp.status_code in (200, 201):
        await hello_message(message)
        # await message.answer("✅ Application submitted successfully!")
    else:
        await message.answer(f"❌ Error submitting application: {resp.text}")

    os.remove(tmp.name)
    await state.clear()
