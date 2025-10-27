# telegram_bot/handlers/start.py
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram import F
from telegram_bot.utils import has_agreed_to_pdn, get_user_by_telegram_id, is_user_admin
from telegram_bot.keyboards import get_consent_keyboard, get_main_user_keyboard, get_main_admin_keyboard
from telegram_bot.states import AuthStates
from accounts.models import PendingTelegramConsent
from django.utils import timezone

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    telegram_id = message.from_user.id
    # Проверяем согласие через профиль
    if not has_agreed_to_pdn(telegram_id):
        # Проверяем, есть ли временное согласие
        pending_consent = PendingTelegramConsent.objects.filter(telegram_id=telegram_id, processed=False).exists()
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
        # Проверяем, авторизован ли пользователь (email подтвержден)
        user = get_user_by_telegram_id(telegram_id)
        if user:
             from telegram_bot.keyboards import get_main_user_keyboard, get_main_admin_keyboard
             from telegram_bot.utils import is_user_admin
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
    # Запоминаем согласие во временной таблице
    consent_record, created = PendingTelegramConsent.objects.get_or_create(
        telegram_id=telegram_id
    )
    consent_record.agreed_at = timezone.now()
    consent_record.save()

    # Переходим к вводу email
    await state.set_state(AuthStates.waiting_for_email)
    await message.answer("Спасибо за подтверждение! Теперь введите свой email для авторизации.")