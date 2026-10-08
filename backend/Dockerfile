FROM python:3.13.15-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
WORKDIR /app

COPY requirements.txt ./
RUN --mount=type=secret,id=pip_ca_bundle \
    if [ -f /run/secrets/pip_ca_bundle ]; then export PIP_CERT=/run/secrets/pip_ca_bundle; fi; \
    python -m pip install --no-cache-dir --require-hashes -r requirements.txt
RUN useradd --create-home --uid 10001 app
RUN install -d -o app -g app -m 0700 /var/lib/docinsight/sender
COPY --chown=app:app . .
USER app
EXPOSE 8000
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
