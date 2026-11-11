# ---------- Stage 1: build (full image) ----------
FROM python:3.12 AS builder
ENV PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1
WORKDIR /build
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
COPY requirements.txt .
RUN pip install -r requirements.txt

# ---------- Stage 2: runtime (slim image) ----------
FROM python:3.12-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    PORT=3000

# Non-root user with a numeric UID (Kubernetes runAsNonRoot needs a numeric UID to verify)
RUN groupadd --system --gid 10001 appuser \
 && useradd --system --uid 10001 --gid 10001 --no-create-home --shell /usr/sbin/nologin appuser

WORKDIR /app
COPY --from=builder /opt/venv /opt/venv
COPY --chown=10001:10001 . .

USER 10001
EXPOSE 3000

# Production WSGI server (gunicorn), not "manage.py runserver"
ENTRYPOINT ["python", "entrypoint.py"]
CMD ["gunicorn", "-c", "gunicorn.conf.py", "todo_project.wsgi:application"]
