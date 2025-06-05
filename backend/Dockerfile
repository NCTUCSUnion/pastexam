# Dockerfile
FROM python:3.11-slim

WORKDIR /usr/src/app

COPY pyproject.toml uv.lock ./

RUN pip install --upgrade pip \
    && pip install uv \
    && uv sync

COPY . .

ENV PATH="/usr/src/app/.venv/bin:${PATH}"

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
