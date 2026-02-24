FROM python:3.11-slim

WORKDIR /app

RUN pip install uv

COPY . .

RUN uv sync

EXPOSE 8080

CMD ["uv", "run", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]
