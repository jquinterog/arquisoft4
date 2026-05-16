FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY alembic.ini ./
COPY alembic ./alembic
COPY componente_promociones ./componente_promociones

EXPOSE 8000

CMD ["sh", "-c", "alembic upgrade head && uvicorn componente_promociones.main:app --host 0.0.0.0 --port 8000"]
