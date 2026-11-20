FROM ghcr.io/astral-sh/uv:0.13.8-python3.12-trixie-slim@sha256:ee8a8854267a3bd09ac0364420803fb74a069068b5fb279a2cf1df664f7273db

WORKDIR /app
ENV UV_PROJECT_ENVIRONMENT=/opt/venv \
    UV_PYTHON_DOWNLOADS=0 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    REALM_DATA_DIR=/data

COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev --no-install-project --no-cache
COPY core ./core
COPY features ./features
COPY main.py ./
RUN groupadd --gid 10001 realm \
    && useradd --uid 10001 --gid realm --no-create-home realm \
    && mkdir /data && chown realm:realm /data
USER realm
VOLUME ["/data"]
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s --start-period=20s \
    CMD /opt/venv/bin/python -c "from urllib.request import urlopen; urlopen('http://127.0.0.1:8000/healthz', timeout=2)"
CMD ["/opt/venv/bin/python", "main.py", "--host", "0.0.0.0"]
