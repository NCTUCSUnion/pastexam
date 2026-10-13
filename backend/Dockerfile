FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1
# Write logs straight to the container output instead of buffering them
ENV PYTHONUNBUFFERED=1
# Trust X-Forwarded-For from nginx, the only service that can reach the backend
ENV FORWARDED_ALLOW_IPS="*"

ENV UV_LINK_MODE=copy

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project --no-dev

COPY . /app
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev

ENV PATH="/app/.venv/bin:$PATH"

ENTRYPOINT []

# CMD ["fastapi", "dev", "--host", "0.0.0.0", "main.py", "--root-path", "/api"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--root-path", "/api", "--workers", "4"]

