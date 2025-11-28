# telegram_bot/bot/handlers.py
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters
from bot.config import BotConfig
from bot.django_client import DjangoClient
from bot.utils import MessageFormatter
from pathlib import Path  # Добавляем импорт


class BotHandlers:
    """Обработчики команд Telegram бота"""

    def __init__(self):
        self.django_client = DjangoClient()
        self.message_formatter = MessageFormatter()

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start"""
        await update.message.reply_text(BotConfig.MESSAGES['start'])

    async def handle_email(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик ввода email"""
        email = update.message.text.strip().lower()

        # Проверяем пользователя (теперь асинхронно)
        user_data = await self.django_client.verify_admin_by_email(email)

        if not user_data:
            await update.message.reply_text(BotConfig.MESSAGES['email_not_found'])
            return

        if not user_data['is_admin']:
            await update.message.reply_text(BotConfig.MESSAGES['not_admin'])
            return

        # Сохраняем chat_id (теперь асинхронно)
        success = await self.django_client.save_telegram_chat_id(
            user_data['user_id'],
            update.effective_chat.id
        )

        if success:
            await update.message.reply_text(BotConfig.MESSAGES['auth_success'])
        else:
            await update.message.reply_text("❌ Ошибка при сохранении данных")

    async def send_order_notification(self, order_data: dict):
        """Отправляет уведомление о заказе всем администраторам"""
        try:
            from telegram import Bot
            from bot.image_processor import ImageProcessor

            bot = Bot(token=BotConfig.TELEGRAM_TOKEN)

            # Получаем chat_id администраторов (теперь асинхронно)
            admin_chat_ids = await self.django_client.get_admin_chat_ids()

            message_text = self.message_formatter.format_order_message(order_data)

            # Пытаемся получить изображение первого товара
            image_buffer = None
            if order_data['products']:
                first_product = order_data['products'][0]
                if first_product.get('image_path'):
                    print(f"🖼️  Пытаемся загрузить изображение: {first_product['image_path']}")
                    image_buffer = ImageProcessor.prepare_image_for_telegram(
                        first_product['image_path']
                    )

            for chat_id in admin_chat_ids:
                try:
                    if image_buffer:
                        print(f"📤 Отправляем фото для заказа #{order_data['id']} в чат {chat_id}")
                        # Важно: создаем новый buffer для каждого отправления
                        image_buffer.seek(0)  # Сбрасываем позицию буфера
                        await bot.send_photo(
                            chat_id=chat_id,
                            photo=image_buffer,
                            caption=message_text,
                            parse_mode='Markdown'
                        )
                    else:
                        print(f"📤 Отправляем текстовое сообщение для заказа #{order_data['id']} в чат {chat_id}")
                        await bot.send_message(
                            chat_id=chat_id,
                            text=message_text,
                            parse_mode='Markdown'
                        )

                except Exception as e:
                    print(f"❌ Ошибка отправки в чат {chat_id}: {e}")
                    # Пробуем отправить без изображения при ошибке
                    try:
                        await bot.send_message(
                            chat_id=chat_id,
                            text=message_text,
                            parse_mode='Markdown'
                        )
                    except Exception as e2:
                        print(f"❌ Критическая ошибка отправки в чат {chat_id}: {e2}")

        except Exception as e:
            print(f"❌ Error in send_order_notification: {e}")

    def setup_handlers(self, application):
        """Настраивает обработчики команд"""
        application.add_handler(CommandHandler("start", self.start))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_email))