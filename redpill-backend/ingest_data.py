import os
from ingestion.data_loader import DataLoader

def ingest_matrix_data():
    data_loader = DataLoader()
    file_path = os.path.join(os.path.dirname(__file__), 'matrix.txt')
    
    if not os.path.exists(file_path):
        print(f"Error: {file_path} not found. Please make sure matrix.txt is in the redpill-backend directory.")
        return

    print(f"Ingesting data from {file_path}...")
    data_loader.ingest_document(file_path, "txt") # Assuming a 'txt' parser will be added or content handled generically
    print("Data ingestion complete.")

if __name__ == "__main__":
    ingest_matrix_data()