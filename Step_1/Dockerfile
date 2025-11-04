FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-sin \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Install Python packages
RUN pip install --no-cache-dir \
    pytesseract \
    pillow \
    pdf2image \
    pandas \
    openpyxl

# Set working directory
WORKDIR /app

# Keep container running
CMD ["bash"]
