# Automated ETL Pipeline with Docker Compose

Proyek ini adalah sebuah pipeline ETL (Extract, Transform, Load) otomatis yang dirancang untuk mengunduh data perjalanan taksi (*taxi trip data*), melakukan pembersihan dan transformasi data (*data cleaning & lookup*), serta memproduksi data mart yang siap digunakan untuk analisis.

Proyek ini telah dikontainerisasi menggunakan **Docker** dan **Docker Compose** untuk memastikan aplikasi dapat berjalan di lingkungan (*environment*) mana saja secara konsisten tanpa kendala ketergantungan OS.

## Daftar Isi
- [Fitur Utama](#fitur-utama)
- [Struktur Proyek](#struktur-proyek)
- [Teknologi & Dependensi](#teknologi--dependensi)
- [Prasyarat Sistem](#prasyarat-sistem)
- [Cara Penggunaan (Docker)](#cara-penggunaan-docker)
- [Detail Alur Kerja ETL](#detail-alur-kerja-etl)

## Fitur Utama
* **Kontainerisasi Penuh:** Berjalan di dalam Docker untuk isolasi *environment*.
* **Automasi Logging & Error Handling:** Menggunakan Shell Script Linux (`etl_pipeline.sh`) dengan parameter `set -eo pipefail` untuk memantau jalannya program secara *real-time* dan merekam seluruh *output* ke dalam berkas log dengan datetime (WIB).
* **Integrasi Docker Environment Variable Dinamis:** Parameter jalur unduhan data (*data URL*) ditarik secara dinamis melalui *Environment Variable* pada Docker Compose, menghindari penulisan kode kaku (*hardcoded*) dan mempermudah penggantian sumber data secara instan.
* **Manajemen Penyimpanan Berkelanjutan (Docker Volumes Binding):** Hasil ekstraksi data dan berkas automasi log otomatis tersinkronisasi ke penyimpanan lokal komputer melalui *bind mounts*, memastikan data tidak hilang saat kontainer dihancurkan (*stateless container*).
* **Arsitektur Modular Berbasis Objek & Polimorfisme (OOP):** Pemisahan fungsi ETL yang bersih ke dalam modul-modul terpisah menggunakan kelas abstrak (`DataTransformation` via ABC) dan pewarisan kelas (`Transformation`), memastikan kode bersifat *reusable* dan mudah dikembangkan untuk jangka panjang.
* **Ekstraksi Tangguh:** Dilengkapi blok `try-except` untuk menangani kegagalan unduhan jaringan tanpa menghentikan seluruh program secara mendadak.
* **Standardisasi Teks:** Mengubah penamaan kolom bergaya `camelCase` menjadi `snake_case` (misal: `tpepPickupDatetime` menjadi `tpep_pickup_datetime`).
* **Kalkulasi Bisnis Turunan (*Feature Engineering*):** * Menghitung durasi perjalanan taksi (`trip_duration_minutes`) dari selisih waktu jemput dan antar.
  * Mengekstraksi komponen waktu menjadi `pickup_date`, `pickup_day_name`, penanda akhir pekan (`is_weekend`), serta kategorisasi waktu operasional (`time_periode` seperti *Late Night, Morning, Afternoon*, dll).
* **Penyelarasan Kodefikasi Data (*Data Mapping & Enrichment*):** Mengubah kode angka mentah menjadi teks deskriptif pada kolom `payment_type` dan `store_and_fwd_flag` agar data lebih mudah dipahami secara bisnis, serta melakukan otomatisasi *left join* dengan data referensi wilayah taksi (*Taxi Zone Lookup*).
* **Imputasi Nilai Kosong Aman (*Data Quality Imputation*):** Memiliki fungsi otomatis untuk mendeteksi data yang bolong (`NaN`) dan mengisinya dengan nilai aman (`-999` untuk kolom angka dan `'Unknown'` untuk kolom teks) demi menjaga integritas data saat dianalisis.
* **Inspeksi Skema Terstruktur:** Menyediakan fungsi `inspect_dataframe` untuk melakukan audit/pencatatan tipe data (*logging data types*) secara transparan pada terminal sebelum dan sesudah data dimodifikasi.

## Struktur Proyek
```text
Tugas_1/
├── data/                       # Penyimpanan data (Volume terikat, diabaikan oleh Git)
│   ├── extraction/             # Hasil unduhan data mentah (.csv & .parquet)
│   ├── mart/                   # Data ringkasan (Data Mart) siap analisis
│   ├── mart_clean/             # Data Mart versi bersih yang telah dilakukan validasi data quality
│   └── transformed/            # Data hasil pembersihan & prapemrosesan (Staging)
├── logs/                       # Berkas catatan automasi (diabaikan oleh Git)
├── src/                        # Modul logika ETL utama
│   ├── extract.py              # Logika pengambilan data dari sumber luar
│   ├── load.py                 # Logika penyimpanan ke format tujuan / mart
│   └── transform.py            # Logika manipulasi data menggunakan Pandas
├── .dockerignore               # Daftar berkas/folder yang diabaikan Docker
├── .gitignore                  # Daftar berkas/folder yang diabaikan Git
├── docker-compose.yaml         # Orkestrasi kontainer & konfigurasi env variable
├── Dockerfile                  # Cetakan dasar lingkungan Python-slim
├── etl_pipeline.sh             # Shell script penggerak utama & manajemen log
├── main.py                     # Berkas utama untuk menjalankan pipeline
└── requirement.txt             # Kebutuhan library Python (Pandas, PyArrow, Requests)
```

## Teknologi & Dependensi
Core: Python 3.10 (Base Image: python:3.10-slim)
Data Processing: Pandas, PyArrow
Networking: Requests
Orchestration & Tools: Docker, Docker Compose, Linux Bash Shell Script

## Prasyarat Sistem
Sebelum menjalankan proyek ini, pastikan komputer Anda sudah terinstal:
Docker Desktop (termasuk Docker Compose)
Git Bash (jika menggunakan OS Windows untuk eksekusi terminal)

## Cara Penggunaan (Docker)
1. Klon Repositori Ini
    ```bash
    git clone [https://github.com/BayuTriR/etl_pipeline_tugas_1.git](https://github.com/BayuTriR/etl_pipeline_tugas_1.git)
    cd etl_pipeline_tugas_1
2. Jalankan Menggunakan Docker Compose
    docker compose up --build
3. Memeriksa Hasil Output
    Setelah kontainer selesai dieksekusi (exited with code 0):
    File Log: Periksa folder ./logs/ di laptop Anda untuk melihat rekam jejak jalannya pipa data secara mendetail.
    File Data: Periksa sub-folder di dalam ./data/ untuk melihat berkas mentah hasil ekstraksi, data antara (staging), hingga data analitik siap pakai (mart).

## Detail Alur Kerja ETL
1. Tahap Extract
    Program mengunduh dua jenis dataset utama menggunakan metode streaming chunk langsung dari URL yang disediakan:
    Taxi Zone Lookup (Format .csv) -> Disimpan di ./data/extraction/taxi_zone_lookup.csv
    Yellow Tripdata (Format .parquet) -> Disimpan di ./data/extraction/yellow_tripdata_2026-01.parquet
2. Tahap Transform
    Jika semua data berhasil dieksekusi tanpa eror, modul transform.py berbasis kelas OOP akan melakukan manipulasi data:
    Melakukan inspeksi tipe data awal sebelum dimodifikasi.
    Mengubah skema seluruh kolom menjadi huruf kecil dengan pemisah garis bawah (snake_case).
    Melakukan casting tipe data (memaksa kolom waktu menjadi datetime64 dan biaya menjadi float).
    Menghitung nilai kolom baru trip_duration_minutes dari selisih waktu jemput (pickup) dan antar (dropoff).
    Melakukan operasi .merge() (data lookup) untuk menggabungkan data perjalanan dengan referensi zona taksi.
    Melakukan pengecekan akhir tipe data pasca-transformasi.
3. Tahap Load
    Data yang sudah bersih diekspor oleh modul load.py ke folder ./data/transformed/ (sebagai staging area), lalu diintegrasikan lebih lanjut ke folder ./data/mart/ dan ./data/mart_clean/ setelah lolos proses pengujian kualitas data (data quality check).
    Proyek ini dikembangkan sebagai bagian dari Tugas Portofolio Data Engineering.