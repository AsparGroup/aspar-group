FROM python:3.11-slim
WORKDIR /app
COPY services/worker-qa/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt
COPY shared /app/shared
COPY services/worker-qa/app /app/app
ENV PYTHONPATH=/app
EXPOSE 80
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80"]
