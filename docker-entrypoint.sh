#!/bin/bash
set -e

echo "Waiting for database..."
until python -c "
import sys, dj_database_url, psycopg2
import os
cfg = dj_database_url.parse(os.environ.get('DATABASE_URL', ''))
try:
    psycopg2.connect(dbname=cfg['NAME'], user=cfg['USER'], password=cfg['PASSWORD'], host=cfg['HOST'], port=cfg['PORT'])
except Exception as e:
    sys.exit(1)
"; do
  sleep 1
done
echo "Database is up."

python manage.py migrate --noinput

exec python manage.py runserver 0.0.0.0:8000