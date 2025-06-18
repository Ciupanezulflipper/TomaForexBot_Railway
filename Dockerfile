FROM python:3.10-slim

# Prevent Python from writing .pyc files and buffer logs
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Install system dependencies (if needed by your libs)
RUN apt-get update \
    && apt-get install -y gcc libffi-dev libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Copy the app code
COPY . .

# Expose a port (not needed for worker, but harmless)
EXPOSE 8000

# Let Render use Procfile to choose entrypoint
CMD ["sleep", "infinity"]
