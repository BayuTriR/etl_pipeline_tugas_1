import pandas as pd
from abc import ABC, abstractmethod
import requests
import os

class DataExtraction(ABC):
    def __init__(self, path: str, output_path: str):
        self.path = path
        self.path_data = output_path
    
    def checking_output_folder(self):
        folder_path = os.path.dirname(self.path_data)

        if folder_path and not os.path.exists(folder_path):
            print(f"Folder '{folder_path}' tidak ditemukan. Membuat folder baru...")
            os.makedirs(folder_path, exist_ok=True)

    def download_file(self):
        response = requests.get(self.path, stream=True)

        if response.status_code != 200:
            raise ConnectionError(f"Gagal download FILE. Status: {response.status_code}")
        
        with open(self.path_data, "wb") as f:
            for file in response.iter_content(chunk_size=8192):
                f.write(file)
        print(f"File berhasil disimpan di: {self.path_data}")

    @abstractmethod
    def extract_data(self):
        pass

class URLextractionCSV(DataExtraction):
    def extract_data(self):
        print(f"\nMengunduh file CSV dari URL: {self.path}")
        self.checking_output_folder()
        self.download_file()
        return pd.read_csv(self.path_data)
    
class URLextractionParquet(DataExtraction):
    def extract_data(self):
        print(f"\nMengunduh file Parquet dari URL: {self.path}")
        self.checking_output_folder()
        self.download_file()
        return pd.read_parquet(self.path_data)