# Base image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Work directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY main.py .
COPY datos_búsqueda.sqlite .

# Expose port
EXPOSE 8000

# Start command (Port is dynamic for Render/Railway)
CMD ["python", "main.py"]
