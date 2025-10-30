# telegram_manager_bot/handlers/start.py
from aiogram import Router, types
from aiogram.filters import Command
from telegram_manager_bot.states import AuthStates
from telegram_manager_bot.keyboards import get_main_menu_keyboard
from telegram_manager_bot.utils import is_superuser_by_email_async

# --- ИМПОРТ ДЛЯ АСИНХРОННОЙ РАБОТЫ С DJANGO ORM ---
from asgiref.sync import sync_to_async
from django.contrib.auth.models import User
from accounts.models import UserProfile
# --- /ИМПОРТ ДЛЯ АСИНХРОННОЙ РАБОТЫ С DJANGO ORM ---

router = Router()

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    """Обработчик команды /start. Проверяет авторизацию."""
    print(f"[DEBUG start.py] /start вызван пользователем {message.from_user.id}")
    user_email = message.text.split(maxsplit=1)[1] if len(message.text.split()) > 1 else None

    if user_email:
        is_admin = await is_superuser_by_email_async(user_email)
        if is_admin:
            # Сохраняем telegram_id в UserProfile
            # Используем sync_to_async для синхронных операций ORM
            user = await sync_to_async(User.objects.get)(email=user_email)
            profile, created = await sync_to_async(UserProfile.objects.get_or_create)(user=user)
            profile.telegram_id = message.from_user.id
            await sync_to_async(profile.save)()
            print(f"[DEBUG start.py] Telegram ID {message.from_user.id} привязан к пользователю {user_email}")

            await message.answer("Добро пожаловать, администратор!", reply_markup=get_main_menu_keyboard())
        else:
            await message.answer("Доступ запрещен. Убедитесь, что вы суперпользователь и указали правильный email.")
    else:
        await message.answer("Добро пожаловать! Для авторизации отправьте /start <ваш_email>")
