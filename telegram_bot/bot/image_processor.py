# telegram_bot/bot/image_processor.py
import io
from pathlib import Path
from PIL import Image
from bot.config import BotConfig


class ImageProcessor:
    """Обработчик изображений для Telegram"""

    @staticmethod
    def prepare_image_for_telegram(image_path: Path) -> io.BytesIO:
        """
        Подготавливает изображение для отправки в Telegram
        Сжимает и конвертирует в подходящий формат
        """
        try:
            if not image_path or not image_path.exists():
                return None

            with Image.open(image_path) as img:
                # Конвертируем в RGB если нужно
                if img.mode in ('RGBA', 'P'):
                    img = img.convert('RGB')

                # Сжимаем для Telegram (макс 10MB)
                max_size = (800, 800)
                img.thumbnail(max_size, Image.Resampling.LANCZOS)

                # Сохраняем в buffer
                buffer = io.BytesIO()
                img.save(buffer, format='JPEG', quality=85, optimize=True)
                buffer.seek(0)

                return buffer

        except Exception as e:
            print(f"❌ Error processing image {image_path}: {e}")
            return None

    @staticmethod
    def get_product_image_path(product_name: str) -> Path:
        """
        Ищет путь к изображению продукта
        """
        try:
            image_dir = BotConfig.PRODUCTS_IMAGE_DIR
            if not image_dir.exists():
                return None

            # Ищем файл по имени продукта (упрощенная логика)
            for ext in ['.jpg', '.jpeg', '.png', '.webp']:
                possible_path = image_dir / f"{product_name}{ext}"
                if possible_path.exists():
                    return possible_path

            # Если не нашли по имени, берем первое изображение из директории
            images = list(image_dir.glob('*'))
            return images[0] if images else None

        except Exception as e:
            print(f"❌ Error finding product image: {e}")
            return None