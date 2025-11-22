# bot_admin_auth.py
# pip install python-telegram-bot django

import logging
import os
import django
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

# --- 1. Настройка Django ORM ---
# Убедитесь, что этот скрипт запускается из корня проекта Django
# или настройте sys.path соответствующим образом.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'flower_delivery.settings')
django.setup()

# Импорт моделей Django после setup()
from django.contrib.auth.models import User
from accounts.models import UserProfile
from asgiref.sync import sync_to_async

# --- 2. Настройка логирования ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- 3. Определение состояний FSM ---
AWAITING_EMAIL = 1

# --- 4. Обработчик команды /start ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Отправляет приветственное сообщение и запрашивает email для авторизации.
    """
    user = update.effective_user
    logger.info(f"Пользователь {user.id} (@{user.username}) нажал /start.")

    await update.message.reply_text(
        "Привет! 👋\n"
        "Для авторизации как администратора, пожалуйста, введите ваш email, "
        "который зарегистрирован в системе сайта."
    )

    # Переход к состоянию ожидания email
    return AWAITING_EMAIL

# --- 5. Обработчик ввода email ---
async def awaiting_email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Проверяет введенный email через Django ORM.
    """
    user = update.effective_user
    email = update.message.text.strip()
    logger.info(f"Пользователь {user.id} (@{user.username}) ввел email: {email}")

    # --- Проверка через Django ORM ---
    # Используем sync_to_async для выполнения ORM-запроса в асинхронной функции
    # ВАЖНО: оборачиваем ВЕСЬ вызов, включая .first()
    try:
        # Правильный способ: оборачиваем лямбду или метод, который возвращает результат
        django_user = await sync_to_async(
            lambda: User.objects.filter(email__iexact=email, is_staff=True).first()
        )()

        if django_user:
            # --- Успешная авторизация ---
            logger.info(f"Пользователь {user.id} (@{user.username}) успешно авторизован как админ: {django_user.email}")

            # Сохраняем связь Telegram ID с Django User через UserProfile
            user_profile, created = await sync_to_async(UserProfile.objects.get_or_create)(user=django_user)
            user_profile.telegram_chat_id = user.id
            await sync_to_async(user_profile.save)()

            # Отправляем сообщение об успешной авторизации
            await update.message.reply_text(
                f"✅ Авторизация успешна!\n"
                f"Добро пожаловать, администратор {django_user.username}! 🎉\n"
                f"Теперь бот будет уведомлять вас о новых заказах."
            )
            # Возвращаем ConversationHandler в начальное состояние (завершаем FSM)
            return ConversationHandler.END
        else:
            # --- Неудачная авторизация ---
            logger.info(f"Пользователь {user.id} (@{user.username}) ввел неверный email: {email}")
            await update.message.reply_text(
                "❌ Авторизация не удалась.\n"
                "Возможные причины:\n"
                "- Email не найден в системе.\n"
                "- У пользователя нет прав администратора.\n"
                "Пожалуйста, проверьте email и попробуйте снова."
            )
            # Возвращаем ConversationHandler в начальное состояние (завершаем FSM)
            return ConversationHandler.END

    except Exception as e:
        # Обработка возможных ошибок ORM
        logger.error(f"Ошибка при проверке email {email} для пользователя {user.id}: {e}")
        await update.message.reply_text(
            "Произошла ошибка при проверке email. Пожалуйста, попробуйте позже."
        )
        return ConversationHandler.END

# --- 6. Глобальная переменная для хранения экземпляра Application ---
# Это позволяет вызывать send_order_notification из других частей кода (например, из Django)
# или передавать application в функцию отправки.
_application_instance = None

def set_application_instance(app):
    """Функция для установки глобальной переменной application."""
    global _application_instance
    _application_instance = app
    logger.info("Application instance установлен для уведомлений.")

def get_application_instance():
    """Функция для получения глобальной переменной application."""
    return _application_instance

# --- 7. Основная функция запуска бота ---
def main():
    """
    Запускает бота с обработчиками.
    """
    # Замените 'YOUR_TELEGRAM_BOT_TOKEN_HERE' на реальный токен вашего бота
    TOKEN = "8264560601:AAG952YYowv9_NFEwdNfVSvfqTfuuYjBQ9M"

    # Создание Application
    application = ApplicationBuilder().token(TOKEN).build()

    # Устанавливаем глобальную переменную application
    set_application_instance(application)

    # Создание ConversationHandler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            AWAITING_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, awaiting_email)],
        },
        fallbacks=[],  # Нет отдельного обработчика отмены
    )

    # Добавление ConversationHandler в Application
    application.add_handler(conv_handler)

    # Запуск polling
    logger.info("Бот запускается...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()