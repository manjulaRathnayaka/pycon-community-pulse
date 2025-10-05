FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy service code and shared module
COPY main.py .
COPY ca-85f67baa-6594-4397-b2a4-59b362a01435.pem .
COPY shared ./shared

# Create non-root user with UID in required range
RUN useradd -u 10004 -m appuser && chown -R appuser:appuser /app
USER 10004

# Run the collector
CMD ["python", "main.py"]
