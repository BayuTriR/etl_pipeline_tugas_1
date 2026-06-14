import pandas as pd
from abc import ABC, abstractmethod
import os

class DataLoad(ABC):
    def __init__(self, list_of_df: list):
        self.list_of_df = list_of_df
        self.mart_dfs = []

    def checking_output_folder(self, output_path: str):
        if output_path and not os.path.exists(output_path):
            print(f"Folder '{output_path}' tidak ditemukan. Membuat folder baru...")
            os.makedirs(output_path, exist_ok=True)

    @abstractmethod
    def load_to_mart(self, output_path: str):
        pass

    @abstractmethod
    def load_to_clean(self, output_path: str):
        pass

class Load(DataLoad):
    def load_to_mart(self, output_path: str):
        self.checking_output_folder(output_path)
    
        min_number_of_columns = min(len(df.columns) for df in self.list_of_df)

        for i, df in enumerate(self.list_of_df):
            df_load = df.copy()
            self.mart_dfs.append(df_load)

            if len(df.columns) > min_number_of_columns:
                file_baru = os.path.join(output_path, "mart_yellow_tripdata.csv")
                df.to_csv(file_baru, index=False)
                print(f"-> Berhasil menyimpan Parquet: {file_baru}")
            # else:
            #     file_baru = os.path.join(output_path, "mart_taxi_zone_lookup.csv")
            #     df.to_csv(file_baru, index=False)
            #     print(f"-> Berhasil menyimpan CSV: {file_baru}")

        print("\nLoad ke data mart berhasil.")
        return self.mart_dfs

    def data_clean(self, df):
        required_cols = ["tpep_pickup_datetime", "tpep_dropoff_datetime", "trip_distance"]
        if all(col in df.columns for col in required_cols):
            print("-> Validasi data quality berdasarkan durasi pickup, dropoff dan trip distance...")
            pickup = pd.to_datetime(df["tpep_pickup_datetime"])
            dropoff = pd.to_datetime(df['tpep_dropoff_datetime'])
            df["error_type"] = "Tidak ada"
            df.loc[df['trip_distance'] <= 0, "error_type"] = "distance invalid"
            df.loc[pickup >= dropoff, "error_type"] = "duration invalid"
        return df

    def load_to_clean(self, output_path: str):
        self.checking_output_folder(output_path)
        min_number_of_columns = min(len(df.columns) for df in self.list_of_df)

        self.transformed_dfs = []
        all_invalid_rows = []

        nama_file_valid = "clean_yellow_tripdata.csv"
        nama_file_invalid = "clean_yellow_tripdata_invalid.csv"

        for i, df in enumerate(self.list_of_df):
            df_evaluated = self.data_clean(df.copy())
            if len(df.columns) > min_number_of_columns:
                df_valid = df_evaluated[df_evaluated["error_type"] == "Tidak ada"]
                df_invalid = df_evaluated[df_evaluated["error_type"] != "Tidak ada"]
                if not df_valid.empty:
                    file_valid = f"{output_path}/{nama_file_valid}"
                    # Jika ini loop pertama (file belum ada), tulis dengan header. Loop berikutnya tinggal append.
                    if not os.path.exists(file_valid):
                        df_valid.to_csv(file_valid, index=False)
                    else:
                        df_valid.to_csv(file_valid, mode='a', header=False, index=False)  
                    print(f"   [VALID] Indeks-{i}: {len(df_valid)} baris berhasil disimpan ke: {file_valid}")
                
                if not df_invalid.empty:
                    all_invalid_rows.append(df_invalid)
                    print(f"   [INVALID] Indeks-{i}: Terdeteksi {len(df_invalid)} baris kotor (ditampung sementara).")
                
                self.transformed_dfs.append(df_evaluated)

        if all_invalid_rows:
            df_all_invalid = pd.concat(all_invalid_rows, ignore_index=True)
            file_invalid_final = f"{output_path}/{nama_file_invalid}"
            
            # Simpan sekaligus jadi satu file csv
            df_all_invalid.to_csv(file_invalid_final, index=False)
            print(f"\n   [SUKSES] Total {len(df_all_invalid)} baris kotor BERHASIL disatukan ke: {file_invalid_final}")
        else:
            print("\n   [INFO] Bersih total! Tidak ditemukan data kotor sama sekali.")
            
        return self.transformed_dfs