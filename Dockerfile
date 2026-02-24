FROM python:3.11-slim

WORKDIR /app

# Install uv
RUN pip install uv

# Copy all files
COPY . .

# Install dependencies
RUN uv sync

# Expose Cloud Run port
EXPOSE 8080

# Run the app (Cloud Run uses port 8080)
CMD ["uv", "run", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]
```
