"""StudyHub 的开发与部署配置；设置在对应课程中逐步解释。"""

import os
from pathlib import Path

import dj_database_url
from django.core.exceptions import ImproperlyConfigured
from django.core.management.utils import get_random_secret_key

BASE_DIR = Path(__file__).resolve().parent.parent

ON_RENDER = os.environ.get("RENDER", "false").lower() == "true"
DEBUG = os.environ.get("DJANGO_DEBUG", "false" if ON_RENDER else "true").lower() == "true"
if ON_RENDER and DEBUG:
    raise ImproperlyConfigured("Render 上必须关闭 DEBUG。")
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY")
if not SECRET_KEY:
    if not DEBUG:
        raise ImproperlyConfigured("关闭 DEBUG 时必须设置 DJANGO_SECRET_KEY。")
    # M0 没有登录会话；M1 加入账号时再配置本地持久密钥。
    SECRET_KEY = get_random_secret_key()

ALLOWED_HOSTS = [
    host.strip()
    for host in os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1,[::1]").split(",")
    if host.strip()
]
RENDER_HOSTNAME = os.environ.get("RENDER_EXTERNAL_HOSTNAME", "").strip()
if RENDER_HOSTNAME and RENDER_HOSTNAME not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(RENDER_HOSTNAME)
if not DEBUG and "*" in ALLOWED_HOSTS:
    raise ImproperlyConfigured("生产环境请指定允许的域名，不能使用 *。")

CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in os.environ.get("DJANGO_CSRF_TRUSTED_ORIGINS", "").split(",")
    if origin.strip()
]
if RENDER_HOSTNAME:
    CSRF_TRUSTED_ORIGINS.append(f"https://{RENDER_HOSTNAME}")

# Render 在 TLS 代理后提供转发头；本地默认不信任来自客户端的该头。
TRUST_PROXY_HEADERS = ON_RENDER or os.environ.get("DJANGO_TRUST_PROXY_HEADERS", "false").lower() == "true"
if TRUST_PROXY_HEADERS:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = not DEBUG
SECURE_REDIRECT_EXEMPT = [r"^health/$"]
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
# 先使用短时间 HSTS；本课不申请浏览器预加载。
SECURE_HSTS_SECONDS = 3600 if not DEBUG else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = not DEBUG

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "core.apps.CoreConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
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
    },
]
WSGI_APPLICATION = "config.wsgi.application"

DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()
if DATABASE_URL:
    try:
        database_config = dj_database_url.parse(
            DATABASE_URL,
            conn_max_age=0,
            conn_health_checks=True,
            ssl_require=os.environ.get("DJANGO_DB_SSL_REQUIRED", "true").lower() == "true",
        )
    except ValueError:
        # 无效连接串也可能包含密码，错误信息不回显连接串。
        raise ImproperlyConfigured("DATABASE_URL 不是有效的 PostgreSQL 连接串。") from None
    if database_config["ENGINE"] != "django.db.backends.postgresql":
        raise ImproperlyConfigured("DATABASE_URL 必须使用 PostgreSQL。")
    DATABASES = {"default": database_config}
elif not DEBUG:
    raise ImproperlyConfigured("生产环境必须设置 Neon PostgreSQL 的 DATABASE_URL。")
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "zh-hans"
TIME_ZONE = "Asia/Shanghai"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
