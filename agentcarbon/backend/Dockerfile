FROM python:3.12-slim

# Install system dependencies required for Tesseract
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy everything else
COPY . /app

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
