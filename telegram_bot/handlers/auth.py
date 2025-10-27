# telegram_bot/handlers/auth.py
from aiogram import Router
from aiogram.types import Message # Добавлен импорт
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from telegram_bot.utils import get_user_by_email_sync, generate_token, send_auth_token_to_email, link_telegram_user_to_django_sync, is_user_admin, check_pending_consent_sync
from telegram_bot.keyboards import get_main_user_keyboard, get_main_admin_keyboard
from telegram_bot.states import AuthStates
from accounts.models import PendingTelegramConsent, UserProfile
from django.utils import timezone
# --- ИМПОРТ ДЛЯ АСИНХРОННОСТИ ---
from asgiref.sync import sync_to_async
# --- /ИМПОРТ ДЛЯ АСИНХРОННОСТИ ---

# Не забудьте импортировать has_agreed_to_pdn_sync в этом файле
from telegram_bot.utils import has_agreed_to_pdn_sync

router = Router()

@router.message(StateFilter(None), lambda message: message.text == "✉️ Авторизоваться по email")
async def prompt_email(message: Message, state: FSMContext):
     # Проверим согласие через PendingTelegramConsent или UserProfile - используем асинхронные версии
     telegram_id = message.from_user.id
     profile_agreed = await has_agreed_to_pdn_sync(telegram_id) # Предполагаем, что has_agreed_to_pdn_sync импортирована
     pending_consent = await check_pending_consent_sync(telegram_id)

     if not profile_agreed and not pending_consent:
         await message.answer("Пожалуйста, сначала подтвердите согласие на обработку ПДн.")
         return

     await state.set_state(AuthStates.waiting_for_email)
     await message.answer("Пожалуйста, введите ваш email для авторизации.")

@router.message(AuthStates.waiting_for_email)
async def process_email(message: Message, state: FSMContext):
    email = message.text.strip()
    if "@" not in email or "." not in email:
        await message.answer("Пожалуйста, введите корректный email адрес.")
        return

    user = await get_user_by_email_sync(email) # Вызов асинхронной функции
    if not user:
        await message.answer("Пользователь с таким email не найден.")
        return

    telegram_id = message.from_user.id

    # Проверяем, было ли согласие через PendingTelegramConsent
    consent_record = await sync_to_async(PendingTelegramConsent.objects.filter(telegram_id=telegram_id, processed=False).first)()
    if consent_record:
        # Обновляем флаг в профиле - используем sync_to_async
        profile, created = await sync_to_async(UserProfile.objects.get_or_create)(user=user)
        profile.telegram_agreed_to_pdn = True
        await sync_to_async(profile.save)()
        consent_record.processed = True
        await sync_to_async(consent_record.save)()
    else:
        # Проверяем, есть ли согласие в профиле (означает, что согласие было дано на сайте)
        try:
            profile = await sync_to_async(UserProfile.objects.get)(user=user)
            if not profile.telegram_agreed_to_pdn:
                 await message.answer("Вы не дали согласия на обработку ПДн для Telegram. Пожалуйста, дайте согласие в вашем профиле на сайте.")
                 return
        except UserProfile.DoesNotExist:
             # Профиля нет, но пользователь есть. Странно. Создаем с False.
             await message.answer("Вы не дали согласия на обработку ПДн для Telegram. Пожалуйста, дайте согласие в вашем профиле на сайте.")
             return


    token = generate_token()
    success = send_auth_token_to_email(email, token)
    if not success:
        await message.answer("Ошибка при отправке токена. Пожалуйста, попробуйте позже.")
        return

    # Сохраняем токен и email в состояние
    await state.update_data(email=email, token=token, user_id=user.id)
    await state.set_state(AuthStates.waiting_for_token)
    await message.answer(f"Токен отправлен на {email}. Пожалуйста, введите его для завершения авторизации.")

@router.message(AuthStates.waiting_for_token)
async def process_token(message: Message, state: FSMContext):
    input_token = message.text.strip()
    data = await state.get_data()
    stored_token = data.get('token')
    email = data.get('email')
    user_id = data.get('user_id')

    if input_token != stored_token:
        await message.answer("Неверный токен. Попробуйте снова.")
        # Можно добавить ограничение на количество попыток
        return

    # Находим пользователя и связываем с Telegram - используем асинхронную версию
    try:
        user = await sync_to_async(User.objects.get)(id=user_id)
        telegram_id = message.from_user.id
        await link_telegram_user_to_django_sync(telegram_id, user) # Вызов асинхронной функции

        # Приветствие и главная клавиатура
        if is_user_admin(user):
             await message.answer(f"Добро пожаловать, администратор {user.username}!", reply_markup=get_main_admin_keyboard())
        else:
             await message.answer(f"Добро пожаловать, {user.username}!", reply_markup=get_main_user_keyboard())

        # Сбрасываем состояние
        await state.clear()

    except User.DoesNotExist:
        await message.answer("Ошибка авторизации. Пользователь не найден.")
        await state.clear()
