FROM ghcr.io/astral-sh/uv:0.13.9 AS uv
FROM python:3.12.10-slim

COPY --from=uv /uv /usr/local/bin/uv
WORKDIR /app

COPY pyproject.toml uv.lock README.md ./
RUN uv sync --locked --no-dev --no-install-project

COPY src ./src
COPY corpus ./corpus
RUN uv sync --locked --no-dev
RUN useradd --create-home --uid 10001 appuser
USER appuser
# Owned by appuser, so a fresh named volume mounted here is writable for the reranker cache.
RUN mkdir -p /home/appuser/fastembed

EXPOSE 8000
ENTRYPOINT ["/app/.venv/bin/openusd-assistant"]
CMD ["serve", "--host", "0.0.0.0"]
