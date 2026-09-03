FROM python:3.11-slim

WORKDIR /workspace

# Install system dependencies if any are needed
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file and install
COPY repackai/backend/requirements.txt /workspace/repackai/backend/requirements.txt
RUN pip install --no-cache-dir -r /workspace/repackai/backend/requirements.txt

# Copy the rest of the application
COPY repackai/ /workspace/repackai/

# Expose port
EXPOSE 8000

# Set Python Path
ENV PYTHONPATH=/workspace

# Set working directory to project root or scripts folder to run seed if needed
WORKDIR /workspace

CMD ["uvicorn", "repackai.backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
