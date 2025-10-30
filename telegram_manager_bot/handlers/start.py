# telegram_manager_bot/handlers/start.py
from aiogram import Router, types
from aiogram.filters import Command
from telegram_manager_bot.utils import get_user_by_telegram_id_sync, is_user_manager, get_user_by_email_sync, link_manager_telegram_id_sync
from telegram_manager_bot.keyboards import get_manager_main_keyboard
from asgiref.sync import sync_to_async

router = Router()

async def send_manager_keyboard(message: types.Message):
    keyboard = get_manager_main_keyboard()
    await message.answer("Меню:", reply_markup=keyboard)

@router.message(Command(commands=['start']))
async def cmd_start(message: types.Message):
    telegram_id = message.from_user.id
    user = await get_user_by_telegram_id_sync(telegram_id)

    if user and is_user_manager(user):
        await message.answer(f"Добро пожаловать, управляющий {user.username}! Вы авторизованы.")
        await send_manager_keyboard(message)
    else:
        await message.answer("Добро пожаловать! Для доступа к функциям управляющего, пожалуйста, зарегистрируйтесь, указав ваш email (тот, что на сайте). Используйте команду /register_manager <ваш_email>")

@router.message(Command(commands=['register_manager']))
async def cmd_register_manager(message: types.Message):
    telegram_id = message.from_user.id
    args = message.text.split(maxsplit=1)
    if len(args) != 2:
        await message.answer("Пожалуйста, используйте команду: /register_manager <ваш_email>")
        return

    email = args[1].strip()

    user = await get_user_by_email_sync(email)
    if not user:
        await message.answer("Пользователь с таким email не найден.")
        return

    if not user.is_superuser:
        await message.answer("У вас нет прав управляющего (суперюзера).")
        return

    success = await link_manager_telegram_id_sync(telegram_id, user)
    if success:
        await message.answer(f"Вы успешно зарегистрированы как управляющий. Добро пожаловать, {user.username}!")
        await send_manager_keyboard(message)
    else:
        await message.answer("Произошла ошибка при регистрации.")