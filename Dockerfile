# Base image Python
FROM python:3.10-slim

# Set working directory utama di dalam container
WORKDIR /app

# Copy file requirements
COPY requirement.txt .

# Install library Python
RUN pip install --no-cache-dir -r requirement.txt

# Copy seluruh source code dari laptop ke dalam container
COPY . .

# Dokumentasi port yang digunakan aplikasi
EXPOSE 8080

# Perintah untuk menjalankan script utama ETL Anda
CMD ["bash", "etl_pipeline.sh"]