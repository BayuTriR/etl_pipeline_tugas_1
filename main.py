from src.extract import URLextractionCSV, URLextractionParquet
from src.transform import Transformation
from src.load import Load
from datetime import datetime

def log_message(message):
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"{current_time} - {message}")

if __name__ == "__main__":
    file_config = [
        {
            "nama": "Data Taxi Zone Lookup",
            "path": "https://d37ci6vzurychx.cloudfront.net/misc/taxi_zone_lookup.csv",
            "output_path": "data/extraction/taxi_zone_lookup.csv",
            "type": "csv"
        },
        {
            "nama": "Data Yellow Tripdata 2026-01",
            "path": "https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2026-01.parquet",
            "output_path": "data/extraction/yellow_tripdata_2026-01.parquet",
            "type": "parquet"
        }
    ]

    data_extracted = []
    log_message("Starting pipeline\n\n")

    # ==============================================================================
    # PROSES EXTRACT
    # ==============================================================================
    print("--- MEMULAI PROSES EXTRACT ---\n")

    log_message("Running extract")

    for config in file_config:
        try:
            if config["type"] == "csv":
                extraction = URLextractionCSV(config["path"], config["output_path"])
            elif config["type"] == "parquet":
                extraction = URLextractionParquet(config["path"], config["output_path"])
            else:
                print(f"Format {config['type']} belum tersedia")
                continue
            
            df = extraction.extract_data()
            data_extracted.append(df)
            print("Proses extract berhasil")
            print(f"[HEADER] Kolom pada {config['nama']}:")
            print(list(df.columns))
        
        except Exception as e:
            print(f"Gagal mengekstrak {config['path']}. Error: {e}\n")

    print(f"\nTotal DataFrame yang masuk tahap EXTRACT: {len(data_extracted)}\n")

    log_message("Extract completed\n")

    print("--- PROSES EXTRACT SELESAI ---\n\n")
    
    # ==============================================================================
    # PROSES TRANSFORM
    # ==============================================================================
    print("--- MEMULAI PROSES TRANSFORM ---\n")

    log_message("Running transform")

    if len(data_extracted) == len(file_config):    
        df_lookup_raw = next((df for df in data_extracted if any(col.lower() == "locationid" for col in df.columns)), None)
        if df_lookup_raw is None:
            print("Data lookup tidak ditemukan di data_extracted")

        transformation = Transformation(data_extracted, df_lookup=df_lookup_raw)
        
        df_trip_raw = next((df for df in data_extracted if "tpep_pickup_datetime" in df.columns or "tpepPickupDatetime" in df.columns), None)
        if df_trip_raw is not None:
            transformation.inspect_dataframe(df=df_trip_raw, stage="Sebelum Transform")

        data_transformed = transformation.clean_data(output_path="data/transformed")

        df_trip_transformed = next((df for df in data_transformed if "tpep_pickup_datetime" in df.columns), None)
        if df_trip_transformed is not None:
            transformation.inspect_dataframe(df=df_trip_transformed, stage="Setelah Transform")
        
        log_message("Transform completed")

        print("\nKolom CSV setelah transform:")
        print(list(data_transformed[0].columns))
       
        print("\nKolom Parquet setelah transform:")
        print(list(data_transformed[1].columns))
        print(data_transformed[1].head(3))

        print("\n--- PROSES TRANSFORM SELESAI ---\n\n")
        
        # =====================================================================
        # PROSES LOAD
        # =====================================================================
        print("--- MEMULAI PROSES LOAD ---\n")

        log_message("Running report\n")

        loader = Load(data_transformed)
        data_mart = loader.load_to_mart(output_path="data/mart")

        print("\n")
        log_message("Report completed\n")

        log_message("Running data quality check\n")

        data_clean = loader.load_to_clean(output_path="data/mart_clean")

        log_message("Data quality check completed")

        print("\n--- PROSES LOAD SELESAI ---\n")
    else:
        print("⚠️ Proses Transform dibatalkan karena data hasil extract tidak lengkap.")
