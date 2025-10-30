import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'your-secret-key-here'
DEBUG = True
ALLOWED_HOSTS = ['localhost', '127.0.0.1']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'shop',
    'accounts',
    'analytics',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'flower_delivery.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                # --- Добавляем наш процессор ---
                'shop.context_processors.cart_count',
            ],
        },
    },
]

WSGI_APPLICATION = 'flower_delivery.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# --- АУТЕНТИФИКАЦИЯ ---
# Указываем кастомные бэкенды аутентификации
AUTHENTICATION_BACKENDS = [
    'accounts.backends.EmailBackend', # Наш бэкенд (вход по email)
    'django.contrib.auth.backends.ModelBackend', # Стандартный бэкенд (вход по username)
]
# --- /АУТЕНТИФИКАЦИЯ ---

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# --- ЯЗЫК И ВРЕМЕННАЯ ЗОНА ---
LANGUAGE_CODE = 'ru-ru'  # <-- Изменено на русский
TIME_ZONE = 'Europe/Moscow'
USE_I18N = True  # <-- Включено для поддержки перевода
USE_TZ = True
# --- /ЯЗЫК И ВРЕМЕННАЯ ЗОНА ---

# --- EMAIL (Yandex) ---
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.yandex.ru'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
# Замените 'your_yandex_email@yandex.ru' на ваш реальный адрес
EMAIL_HOST_USER = 'wotbotov@yandex.ru'  # Ваш email на Yandex
# Вместо обычного пароля используйте "Пароль приложения"
# или "Специальный пароль" (в зависимости от настроек безопасности Yandex)
EMAIL_HOST_PASSWORD = 'ahdrzztzdsgaupzj' # Пароль приложения
DEFAULT_FROM_EMAIL = 'otbotov@yandex.ru'
# --- /EMAIL ---

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# 152-ФЗ: Логирование обработки ПДн
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'pdn.log',
        },
    },
    'loggers': {
        'pdn': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}

TELEGRAM_MANAGER_BOT_TOKEN = '8253880822:AAHG9xrZlljOw0TTErZKivMDe4mtp1HH3c4'