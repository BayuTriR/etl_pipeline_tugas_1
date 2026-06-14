#!/bin/bash
set -eo pipefail

# Ambil direktori project saat ini
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

# Buat folder logs jika belum ada
mkdir -p ./logs

# Nama file log menggunakan timestamp per hari
LOG_FILE="./logs/pipeline_$(date "+%Y-%m-%d %H:%M:%S").log"

# Jalankan python, gabungkan output error (2>&1), 
# lalu tampilkan di terminal sekaligus simpan ke file log (tee -a)
python main.py 2>&1 | tee -a "$LOG_FILE"