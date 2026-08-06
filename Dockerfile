FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir \
    pycryptodome click rich textual fastapi uvicorn

COPY server/ ./server/
COPY common/ ./common/
COPY cli.py ./

EXPOSE 4444 5555 8080

VOLUME ["/app/loot"]

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python3 -c "import sys; sys.exit(0)"

ENTRYPOINT ["python3", "cli.py", "server"]
