import os
import pandas as pd



# Show all the columns  of the csv files in the dataset folder
dataset_folder = 'dataset'

if os.path.exists(dataset_folder):
    for filename in os.listdir(dataset_folder):
        if filename.endswith(".csv"):
            filepath = os.path.join(dataset_folder, filename)
            try:
                # read only the first row to get columns quickly
                df = pd.read_csv(filepath, nrows=0)
                print(f"File: {filename}")
                print(f"Columns: {list(df.columns)}")
                print("-" * 40)
            except Exception as e:
                print(f"Error reading {filename}: {e}")
else:
    print(f"Folder '{dataset_folder}' does not exist.")