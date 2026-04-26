from pathlib import Path
from datetime import timedelta
import os
import dj_database_url

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent


# ========================
# SECURITY & DEBUG
# ========================
SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key")

DEBUG = True  # 🔥 TEMP ENABLE FOR DEBUG (later set False)

ALLOWED_HOSTS = ["*"]


# ========================
# CORS CONFIG
# ========================
CORS_ALLOW_ALL_ORIGINS = True  # 🔥 for now (later restrict)

CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://playto-qosopqugf-paridhis-projects-066e3ee2.vercel.app",
]

CSRF_TRUSTED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://playto-qosopqugf-paridhis-projects-066e3ee2.vercel.app",
]


# ========================
# APPS
# ========================
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework.authtoken",
    "corsheaders",
    "users",
    "kyc",
]


# ========================
# MIDDLEWARE
# ========================
MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


# ========================
# URLS
# ========================
ROOT_URLCONF = "config.urls"


# ========================
# TEMPLATES
# ========================
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]


# ========================
# WSGI
# ========================
WSGI_APPLICATION = "config.wsgi.application"


# ========================
# DATABASE
# ========================
DATABASE_URL = os.environ.get("DATABASE_URL")

if DATABASE_URL:
    DATABASES = {
        "default": dj_database_url.parse(DATABASE_URL)
    }
else:
    # 🔥 fallback for local
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }


# ========================
# PASSWORD VALIDATION
# ========================
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# ========================
# INTERNATIONALIZATION
# ========================
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True


# ========================
# STATIC & MEDIA
# ========================
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"


# ========================
# CUSTOM USER
# ========================
AUTH_USER_MODEL = "users.User"


# ========================
# DRF SETTINGS
# ========================
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.TokenAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    # ❌ REMOVED EXCEPTION HANDLER FOR DEBUG
}


# ========================
# JWT (optional)
# ========================
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=2),
}


# ========================
# DEFAULT FIELD
# ========================
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"