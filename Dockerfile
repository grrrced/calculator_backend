FROM python:3.12-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    CALCULATOR_HOST=0.0.0.0 \
    CALCULATOR_DB_PATH=/data/calculator.sqlite3

COPY server.py calculator.py database.py ./

EXPOSE 8000

CMD ["python", "server.py"]
