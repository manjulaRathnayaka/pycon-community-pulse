FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy service code and shared module
COPY main.py .
COPY openapi.yaml .
COPY shared ./shared

# Create non-root user with UID in required range
RUN useradd -u 10001 -m appuser && chown -R appuser:appuser /app
USER 10001

# Expose port
EXPOSE 8000

# Run the application
CMD ["python", "main.py"]
