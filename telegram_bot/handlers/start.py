# telegram_bot/handlers/start.py
from aiogram import Router
from aiogram.types import Message # Добавлен импорт
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram import F
from telegram_bot.utils import has_agreed_to_pdn_sync, get_user_by_telegram_id_sync, is_user_admin # Импортируем асинхронную версию
from telegram_bot.keyboards import get_consent_keyboard, get_main_user_keyboard, get_main_admin_keyboard
from telegram_bot.states import AuthStates
from accounts.models import PendingTelegramConsent
from django.utils import timezone
# --- ИМПОРТ ДЛЯ АСИНХРОННОСТИ ---
from asgiref.sync import sync_to_async
# --- /ИМПОРТ ДЛЯ АСИНХРОННОСТИ ---

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    telegram_id = message.from_user.id
    # Проверяем согласие через профиль - используем асинхронную версию
    agreed = await has_agreed_to_pdn_sync(telegram_id) # Вызов асинхронной функции
    if not agreed:
        # Проверяем, есть ли временное согласие - используем sync_to_async
        pending_consent = await sync_to_async(PendingTelegramConsent.objects.filter(telegram_id=telegram_id, processed=False).exists)()
        if not pending_consent:
            await message.answer(
                "Для использования бота необходимо согласиться с политикой обработки персональных данных.",
                reply_markup=get_consent_keyboard()
            )
        else:
            # Если есть временное согласие, сразу просим email
            await state.set_state(AuthStates.waiting_for_email)
            await message.answer("Вы уже подтвердили согласие. Теперь введите свой email для авторизации.")
    else:
        # Проверяем, авторизован ли пользователь (email подтвержден) - используем асинхронную версию
        user = await get_user_by_telegram_id_sync(telegram_id) # Вызов асинхронной функции
        if user:
             from telegram_bot.keyboards import get_main_user_keyboard, get_main_admin_keyboard
             # is_user_admin не взаимодействует с БД, можно вызывать синхронно
             if is_user_admin(user):
                 await message.answer(f"Добро пожаловать, администратор {user.username}!", reply_markup=get_main_admin_keyboard())
             else:
                 await message.answer(f"Добро пожаловать, {user.username}!", reply_markup=get_main_user_keyboard())
        else:
            await message.answer("Для начала работы, пожалуйста, авторизуйтесь по email.", reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="✉️ Авторизоваться по email")]], resize_keyboard=True))
            await state.set_state(AuthStates.waiting_for_email)

# Обработчик согласия на ПДн
@router.message(F.text == "✅ Принимаю политику обработки ПДн")
async def handle_consent(message: Message, state: FSMContext):
    telegram_id = message.from_user.id
    # Запоминаем согласие во временной таблице - используем sync_to_async
    consent_record, created = await sync_to_async(PendingTelegramConsent.objects.get_or_create)(
        telegram_id=telegram_id
    )
    consent_record.agreed_at = timezone.now()
    await sync_to_async(consent_record.save)() # Сохранение тоже синхронная операция

    # Переходим к вводу email
    await state.set_state(AuthStates.waiting_for_email)
    await message.answer("Спасибо за подтверждение! Теперь введите свой email для авторизации.")