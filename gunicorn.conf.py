import os

bind = f"0.0.0.0:{os.environ.get('PORT', '3000')}"
worker_class = "gthread"
workers = int(os.environ.get("GUNICORN_WORKERS", "3"))
threads = int(os.environ.get("GUNICORN_THREADS", "2"))
timeout = 30
graceful_timeout = 30
accesslog = "-"
errorlog = "-"
