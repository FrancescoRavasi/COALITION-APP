"""
settings_rpi.py — Override settings per Raspberry Pi 3 deployment.

Importa tutte le impostazioni base e sovrascrive solo ciò che è necessario
per il deployment LAN-only su RPi3 con Docker Compose + PostgreSQL.
"""

import os

# --- Base settings ---
from gotta_bike_platform.settings import *  # noqa: F401, F403

# ---------------------------------------------------------------------------
# Core
# ---------------------------------------------------------------------------

DEBUG = False

# Hosts LAN: imposta via ALLOWED_HOSTS nel .env / docker-compose
# Esempio: "192.168.1.100,localhost,127.0.0.1"
_allowed = os.environ.get("ALLOWED_HOSTS", "localhost,127.0.0.1")
ALLOWED_HOSTS = [h.strip() for h in _allowed.split(",") if h.strip()]

# Nessun Railway su RPi — rimuovi la logica private-domain
RAILWAY_PRIVATE_DOMAIN = ""

# ---------------------------------------------------------------------------
# Sicurezza — LAN only, niente SSL forzato
# ---------------------------------------------------------------------------
SECURE_SSL_REDIRECT = False
SECURE_PROXY_SSL_HEADER = None
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_HSTS_SECONDS = 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = False

# ---------------------------------------------------------------------------
# Database — PostgreSQL via DATABASE_URL
# ---------------------------------------------------------------------------
import dj_database_url  # noqa: E402

_db_url = os.environ.get("DATABASE_URL", "postgresql://coalition:password@db:5432/coalition")
DATABASES = {
    "default": dj_database_url.parse(_db_url, conn_max_age=600)
}

# ---------------------------------------------------------------------------
# Cache — LocMemCache (niente Redis su RPi3)
# ---------------------------------------------------------------------------
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "coalition-rpi",
    }
}

# ---------------------------------------------------------------------------
# App installate — rimuovi apps.zwift (zauth OAuth)
# ---------------------------------------------------------------------------
INSTALLED_APPS = [
    app for app in INSTALLED_APPS  # noqa: F405
    if app != "apps.zwift.apps.ZwiftConfig"
]

# ---------------------------------------------------------------------------
# File statici e media
# ---------------------------------------------------------------------------
STATIC_ROOT = "/app/staticfiles"
MEDIA_ROOT = "/app/media"
MEDIA_URL = "/media/"

# ---------------------------------------------------------------------------
# Logfire — disabilita se il token non è configurato
# ---------------------------------------------------------------------------
import logfire  # noqa: E402

_logfire_token = os.environ.get("LOGFIRE_TOKEN", "")
if not _logfire_token:
    # Reimposta logfire senza token → nessun dato inviato al cloud
    logfire.configure(
        service_name="coalition-rpi",
        send_to_logfire=False,
    )
