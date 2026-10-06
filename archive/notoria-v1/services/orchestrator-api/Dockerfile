FROM python:3.11-slim
WORKDIR /app
COPY services/orchestrator-api/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt
COPY shared /app/shared
COPY services/orchestrator-api/app /app/app
COPY services/orchestrator-api/alembic /app/alembic
COPY services/orchestrator-api/alembic.ini /app/alembic.ini
ENV PYTHONPATH=/app
EXPOSE 8000
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
