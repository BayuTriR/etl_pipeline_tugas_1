import pandas as pd
from abc import ABC, abstractmethod
import os
import re

class DataTransformation(ABC):
    def __init__(self, list_of_df: list):
        self.list_of_df = list_of_df
        self.transformed_dfs = []

    def camel_to_snake(self, column_name):
        string = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', column_name)
        string = re.sub('(.)([0-9]+)', r'\1_\2', column_name)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', string).lower()
        # return re.sub(r'(?<=[a-z0-9])(?=[A-Z])', '_', column_name).lower().replace('__', '_')
    
    def checking_output_folder(self, output_path: str):
        if output_path and not os.path.exists(output_path):
            print(f"Folder '{output_path}' tidak ditemukan. Membuat folder baru...")
            os.makedirs(output_path, exist_ok=True)
    
    @abstractmethod
    def transform_process(self, df) :
        pass

    @abstractmethod
    def save_data(self, df, output_path: str, number_of_columns: int):
        pass
        
    def clean_data(self, output_path: str):
        self.checking_output_folder(output_path)

        min_number_of_columns = min(len(df.columns) for df in self.list_of_df)

        for i, df in enumerate(self.list_of_df):
            print(f"\nMelakukan transformasi data pada DataFrame indeks ke-{i}...")

            df.columns = [self.camel_to_snake(col) for col in df.columns]

            df = self.transform_process(df)
            
            self.transformed_dfs.append(df)

            self.save_data(df, output_path, min_number_of_columns)
        
        print("\nSemua transformasi data berhasil.")
        return self.transformed_dfs
    
class Transformation(DataTransformation):
    def __init__(self, list_of_df: list, df_lookup: pd.DataFrame):
        super().__init__(list_of_df)
        # Samakan nama kolom lookup menjadi snake_case agar match saat join
        self.df_lookup = df_lookup.copy()
        self.df_lookup.columns = [self.camel_to_snake(col) for col in self.df_lookup.columns]

    def transform_process(self, df):
        # Konversi Datetime
        df = self.convert_datetime(df)
        # Konversi Numeric / Float
        df = self.convert_numeric(df)
        # Hitung Durasi Trip
        df = self.trip_duration(df)
        # Tentukan Tanggal Pickup
        df = self.pickup_date(df)
        # Tentukan Hari Pickup
        df = self.pickup_day_name(df)
        # Tentukan Is Weekend
        df = self.is_weekend(df)
        # Tentukan Time Periode
        df = self.time_periode(df)
        # Konversi Payment Type
        df = self.transform_payment_type(df)
        # Konversi Store And Forward
        df = self.transform_store_and_fwd_flag(df)
        # Join Location
        df = self.join_location_lookup(df)
        # Konversi Is NaN
        df = self.convert_is_nan(df)
        return df
    
    def inspect_dataframe(self, df, stage: str):
        print(f"\n=== PENGECEKAN TIPE DATA ({stage.upper()}) ===")
        
        datetime_cols = ["tpep_pickup_datetime", "tpep_dropoff_datetime"]
        float_cols = ["fare_amount", "tip_amount", "total_amount"]
        
        print("--- Tipe Data Datetime ---")
        for col in datetime_cols:
            if col in df.columns:
                print(f"Kolom {col}: {df[col].dtype}")
                
        print("\n--- Tipe Data Float / Numeric ---")
        for col in float_cols:
            if col in df.columns:
                print(f"Kolom {col}: {df[col].dtype}")
        print("=======================================================")

    def convert_datetime(self, df):
        date_cols = ["tpep_pickup_datetime", "tpep_dropoff_datetime"]
        for col in date_cols:
            if col in df.columns:
                if pd.api.types.is_datetime64_any_dtype(df[col]):
                    print(f"-> Kolom {col} ditemukan & bertipe DATETIME. Tidak dilakukan perubahan tipe data...")
                    continue
                print(f"-> Kolom {col} ditemukan. Mengubah tipe data {col} ke DATETIME...")
                df[col] = pd.to_datetime(df[col])
            else:
                print(f"-> Kolom {col} tidak ditemukan")
        return df

    def convert_numeric(self, df):
        numeric_cols = ["fare_amount", "tip_amount", "total_amount"]
        for col in numeric_cols:
            if col in df.columns:
                if pd.api.types.is_float_dtype(df[col]):
                    print(f"-> Kolom {col} ditemukan & sudah bertipe FLOAT. Tidak dilakukan perubahan tipe data...")
                    continue
                print(f"-> Kolom {col} ditemukan. Mengubah tipe data {col} ke FLOAT...")
                df[col] = df[col].astype(float)
            else:
                print(f"-> Kolom {col} tidak ditemukan")
        return df

    def trip_duration(self, df):
        if "tpep_pickup_datetime" in df.columns and "tpep_dropoff_datetime" in df.columns:
            print("-> Menghitung trip_duration_minutes...")
            pickup = pd.to_datetime(df["tpep_pickup_datetime"])
            dropoff = pd.to_datetime(df['tpep_dropoff_datetime'])
            df['trip_duration_minutes'] = (dropoff - pickup)
        return df
    
    def pickup_date(self, df):
        if "tpep_pickup_datetime" in df.columns:
            print("-> Menentukan pickup_date...")
            pickup = pd.to_datetime(df["tpep_pickup_datetime"])
            df['pickup_date'] = pickup.dt.date
        return df
    
    def pickup_day_name(self, df):
        if "tpep_pickup_datetime" in df.columns:
            print("-> Menentukan pickup_day_name...")
            pickup = pd.to_datetime(df["tpep_pickup_datetime"])
            df['pickup_day_name'] = pickup.dt.day_name()
        return df
    
    def is_weekend(self, df):
        if "tpep_pickup_datetime" in df.columns:
            print("-> Menentukan is_weekend...")
            pickup = pd.to_datetime(df["tpep_pickup_datetime"])
            df['is_weekend'] = pickup.dt.weekday >= 5
        return df
    
    def periode(self, periode):
        if 0 <= periode <= 5:
            return "Late Night"
        elif 5 < periode <= 10:
            return "Morning"
        elif 10 < periode <= 15:
            return "Afternoon"
        elif 15 < periode <= 19:
            return "Evening Rush"
        else:
            return "Night"
        
    def time_periode(self, df):
        if "tpep_pickup_datetime" in df.columns:
            print("-> Menentukan time_periode...")
            pickup = pd.to_datetime(df["tpep_pickup_datetime"])
            df['time_periode'] = pickup.dt.hour.apply(self.periode)
        return df

    def transform_payment_type(self, df):
        if "payment_type" in df.columns:
            print("-> Mengubah kode payment type...")
            payment_type = {
                1: "Credit Card",
                2: "Cash",
                3: "No Charge",
                4: "Dispute",
                0: "Unknown"
            }
            df["payment_type"] = df["payment_type"].map(payment_type)  
        return df

    def transform_store_and_fwd_flag(self, df):
        if "store_and_fwd_flag" in df.columns:
            print("-> Mengubah kode store and fwd flag...")
            store_and_fwd_flag = {
                'Y': "Store and Forward",
                'N': "Normal"
            }
            df["store_and_fwd_flag"] = df["store_and_fwd_flag"].map(store_and_fwd_flag)  
        return df
    
    def convert_is_nan(self, df):   
        numeric_columns = df.select_dtypes(include=["number"]).columns
        df[numeric_columns] = df[numeric_columns].fillna(-999)

        object_columns = df.select_dtypes(include=["object"]).columns
        df[object_columns] = df[object_columns].fillna('Unknown')

        return df

    def join_location_lookup(self, df):
        lookup_key = "location_id"
        if lookup_key not in self.df_lookup.columns:
            self.df_lookup.columns = [self.camel_to_snake(col) for col in self.df_lookup.columns]

        # PROSES JOIN PICKUP
        if "pulocation_id" in df.columns:
            print("-> Melakukan join data untuk PickUp Location...")
            df = df.merge(self.df_lookup, left_on="pulocation_id", right_on=lookup_key, how="left")
            df = df.rename(columns={
                "borough": "pickup_borough",
                "zone": "pickup_zone",
                "service_zone": "pickup_service_zone"
            })
            # Hapus kolom 'location_id'
            if lookup_key in df.columns:
                df = df.drop(columns=[lookup_key])

        # PROSES JOIN DROPOFF
        if "dolocation_id" in df.columns:
            print("-> Melakukan join data untuk DropOff Location...")
            df = df.merge(self.df_lookup, left_on="dolocation_id", right_on=lookup_key, how="left")
            df = df.rename(columns={
                "borough": "dropoff_borough",
                "zone": "dropoff_zone",
                "service_zone": "dropoff_service_zone"
            })
            if lookup_key in df.columns:
                df = df.drop(columns=[lookup_key])
            
        return df
    
    def save_data(self, df, output_path: str, number_of_columns: int):
        if len(df.columns) > number_of_columns:
            file_baru = os.path.join(output_path, "transformed_yellow_tripdata.parquet")
            df.to_parquet(file_baru, index=False)
            print(f"-> Berhasil menyimpan Parquet: {file_baru}")
        # else:
        #     file_baru = os.path.join(output_path, "transformed_taxi_zone_lookup.csv")
        #     df.to_csv(file_baru, index=False)
        #     print(f"-> Berhasil menyimpan CSV: {file_baru}")