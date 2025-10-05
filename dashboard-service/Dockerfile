FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy service code and templates
COPY main.py .
COPY templates ./templates

# Create non-root user with UID in required range
RUN useradd -u 10003 -m appuser && chown -R appuser:appuser /app
USER 10003

# Expose port
EXPOSE 8080

# Run the application
CMD ["python", "main.py"]
