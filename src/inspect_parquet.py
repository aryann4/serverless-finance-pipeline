import pandas as pd
import os

# Define the path to the parquet file
file_path = '../data/transactions.parquet'

# Check if file exists
if not os.path.exists(file_path):
    print(f"ERROR: File not found at {file_path}")
    print("Current working directory:", os.getcwd())
else:
    try:
        # Load the parquet file
        df = pd.read_parquet(file_path)

        print("\n--- SUCCESS: Parquet File Read Successfully ---")
        print(f"Rows: {df.shape[0]}")
        print(f"Columns: {df.shape[1]}")
        print("\n--- First 5 Rows of Data ---")
        print(df.head())
        print("\n--- Column Types ---")
        print(df.dtypes)

    except Exception as e:
        print(f"Error reading file: {e}")