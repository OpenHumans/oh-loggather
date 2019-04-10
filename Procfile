web: gunicorn loggather.wsgi:application
worker: celery worker -A loggather --concurrency 1 -l info