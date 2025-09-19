import os
from pathlib import Path
from urllib.parse import urlparse

BASE_DIR = Path(__file__).resolve().parent.parent

# ── Core env ──────────────────────────────────────────────────────────────────
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "dev-only-change-me")
DEBUG = os.getenv("DJANGO_DEBUG", "False").lower() == "true"

ALLOWED_HOSTS = [h.strip() for h in os.getenv("DJANGO_ALLOWED_HOSTS", "").split(",") if h.strip()] or [
    "127.0.0.1", "localhost"
]

# لو مفيش متغيرات، نضبط localhost افتراضياً عشان Swagger يشتغل
_default_trusted = ["http://localhost:8000", "http://127.0.0.1:8000"]
CSRF_TRUSTED_ORIGINS = [u.strip() for u in os.getenv("CSRF_TRUSTED_ORIGINS", "").split(",") if u.strip()] or _default_trusted

# ── Apps ───────────────────────────────────────────────────────────────────────
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party
    "rest_framework",
    "drf_spectacular",
    "corsheaders",                # ← مهم لـ CORS
    # Local
    "inference",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",      # ← لازم ييجي قبل CommonMiddleware
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "mlapi.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    }
]

WSGI_APPLICATION = "mlapi.wsgi.application"
ASGI_APPLICATION = "mlapi.asgi.application"

# ── Database (SQLite fallback) ────────────────────────────────────────────────
DB_URL = os.getenv("DATABASE_URL", "").strip()
if not DB_URL:
    DATABASES = {
        "default": {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / "db.sqlite3"}
    }
else:
    # دعم صيغ متعددة من مزودي الاستضافة
    DB_URL = DB_URL.replace("postgresql+psycopg://", "postgres://").replace("postgresql+psycopg2://", "postgres://")
    p = urlparse(DB_URL)
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": (p.path or "").lstrip("/"),
            "USER": p.username,
            "PASSWORD": p.password,
            "HOST": p.hostname,
            "PORT": p.port or "5432",
            "CONN_MAX_AGE": 60,
            "OPTIONS": {"sslmode": os.getenv("PGSSLMODE", "prefer")},
        }
    }

# ── i18n / tz ─────────────────────────────────────────────────────────────────
LANGUAGE_CODE = "en-us"
TIME_ZONE = "Africa/Cairo"
USE_I18N = True
USE_TZ = True

# ── Static / media ────────────────────────────────────────────────────────────
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ── DRF + Swagger ─────────────────────────────────────────────────────────────
REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    # للتجربة المريحة
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
    ],
    # أثناء التطوير: أبسط مصادقة وتصريح لتجنّب CSRF في Swagger
    "DEFAULT_AUTHENTICATION_CLASSES": (
        ("rest_framework.authentication.BasicAuthentication",) if DEBUG else
        ("rest_framework.authentication.SessionAuthentication",)
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        ("rest_framework.permissions.AllowAny",) if DEBUG else
        ("rest_framework.permissions.IsAuthenticatedOrReadOnly",)
    ),
}

SPECTACULAR_SETTINGS = {
    "TITLE": "ML Inference API",
    "DESCRIPTION": "Predict endpoint powered by your joblib model.",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": True,
}

# ── CORS ──────────────────────────────────────────────────────────────────────
if DEBUG:
    # التطوير: افتح كل الأصول عشان Swagger/Postman يشتغلوا براحة
    CORS_ALLOW_ALL_ORIGINS = True
    CORS_ALLOW_CREDENTIALS = True
else:
    # الإنتاج: اسمح بس للأصول المحددة (لو عندك دومين)
    CORS_ALLOWED_ORIGINS = [o.strip() for o in os.getenv("CORS_ALLOWED_ORIGINS", "").split(",") if o.strip()]
    CORS_ALLOW_CREDENTIALS = True

# ── Security (when DEBUG=False) ───────────────────────────────────────────────
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = "DENY"
