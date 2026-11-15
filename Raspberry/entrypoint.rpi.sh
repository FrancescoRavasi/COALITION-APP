#!/bin/sh
# entrypoint.rpi.sh — Entrypoint per Raspberry Pi (gunicorn invece di granian)
# Rendi eseguibile con: chmod +x entrypoint.rpi.sh

set -e

# Esegui le migrazioni Django
echo "Running migrations..."
python manage.py migrate

# Seed del dataset Zwift (solo se vuoto, non fatale)
echo "Seeding Zwift route/segment dataset (if empty)..."
python manage.py sync_zwift_data --if-empty || echo "warning: zwift_data seed failed (retry via scheduler / Check for updates)"

# Seed dei pesi vELO2 (solo se vuoti, non fatale)
echo "Seeding vELO2 route factor weights (if empty)..."
python manage.py import_velo_weights --if-empty || echo "warning: vELO seed failed (retry via Load vELO weights)"

# Creazione superuser (solo se DJANGO_SUPERUSER_USERNAME è impostato)
if [ -n "$DJANGO_SUPERUSER_USERNAME" ]; then
  echo "Creating superuser (if not exists)..."
  python manage.py createsuperuser --no-input || true
fi

# Avvia il background task worker
echo "Starting background task worker..."
python manage.py db_worker &

# Avvia lo scheduler (sostituisce un cron esterno)
echo "Starting scheduler..."
python manage.py scheduler &

# Avvia il server con Gunicorn
# 2 worker su RPi3 con 1GB RAM: bilancio tra concorrenza e uso memoria
echo "Starting server with Gunicorn..."
exec gunicorn gotta_bike_platform.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers 2 \
  --timeout 120 \
  --access-logfile - \
  --error-logfile -
