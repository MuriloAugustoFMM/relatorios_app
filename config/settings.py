from pathlib import Path
from decouple import config, Csv

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config("DJANGO_SECRET_KEY", default="dev-key-troque-em-producao")
DEBUG = config("DJANGO_DEBUG", default=True, cast=bool)
ALLOWED_HOSTS = config("DJANGO_ALLOWED_HOSTS", default="localhost,127.0.0.1", cast=Csv())

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "storages",
    "core",
    "checklist",
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
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# ---------------------------------------------------------------------------
# Banco de dados: Postgres rodando no container "db" (ver docker-compose.yml)
# ---------------------------------------------------------------------------
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": config("DB_NAME", default="relatorios"),
        "USER": config("DB_USER", default="relatorios"),
        "PASSWORD": config("DB_PASSWORD", default="relatorios"),
        "HOST": config("DB_HOST", default="db"),
        "PORT": config("DB_PORT", default="5432"),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_TZ = True

# ---------------------------------------------------------------------------
# Arquivos estáticos (CSS/JS do próprio Django admin etc.) — ficam no volume local
# ---------------------------------------------------------------------------
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ---------------------------------------------------------------------------
# Storage de mídia (fotos dos checklists/relatórios): MinIO via django-storages
# Compatível com S3 — se um dia migrar pra nuvem (R2/S3 real), só troca o endpoint.
# ---------------------------------------------------------------------------
STORAGES = {
    "default": {
        "BACKEND": "storages.backends.s3.S3Storage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

AWS_ACCESS_KEY_ID = config("MINIO_ROOT_USER", default="minioadmin")
AWS_SECRET_ACCESS_KEY = config("MINIO_ROOT_PASSWORD", default="minioadmin123")
AWS_STORAGE_BUCKET_NAME = config("MINIO_BUCKET", default="relatorios-fotos")
AWS_S3_ENDPOINT_URL = config("MINIO_ENDPOINT", default="http://minio:9000")
# URL usada para MONTAR os links das imagens (precisa ser acessível pelo navegador do usuário,
# por isso é diferente do endpoint interno usado pelo Django pra conversar com o MinIO).
# Inclui o nome do bucket porque o MinIO usa endereçamento "path-style"
# (http://host/bucket/arquivo), diferente do S3 real (bucket.host/arquivo).
_minio_public_host = config("MINIO_PUBLIC_ENDPOINT", default="http://localhost:9000")
AWS_S3_CUSTOM_DOMAIN = f"{_minio_public_host.replace('http://', '').replace('https://', '')}/{AWS_STORAGE_BUCKET_NAME}"
AWS_S3_URL_PROTOCOL = "http:" if "localhost" in _minio_public_host else "https:"
AWS_S3_ADDRESSING_STYLE = "path"
AWS_S3_FILE_OVERWRITE = False
AWS_DEFAULT_ACL = None
AWS_QUERYSTRING_AUTH = False  # bucket público de leitura (definido no createbuckets do compose)

MEDIA_URL = "media/"