"""Container entrypoint: wait for MariaDB, apply migrations, then start the server (as PID 1)."""
import os
import subprocess
import sys
import time


def migrate_with_retry(attempts=30, delay=2):
    for attempt in range(1, attempts + 1):
        if subprocess.run([sys.executable, "manage.py", "migrate", "--noinput"]).returncode == 0:
            return
        print(f"Database not ready (attempt {attempt}/{attempts}); retrying in {delay}s...", flush=True)
        time.sleep(delay)
    sys.exit("Could not apply migrations: database unreachable.")


if os.environ.get("RUN_MIGRATIONS", "1") == "1":
    migrate_with_retry()

cmd = sys.argv[1:] or ["gunicorn", "-c", "gunicorn.conf.py", "todo_project.wsgi:application"]
os.execvp(cmd[0], cmd)  # replace this process so gunicorn receives SIGTERM directly
