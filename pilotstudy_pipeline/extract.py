"""
Load data from S3 Bucket
Combine the historical data into one csv file
ERD: Museum ERD
"""
from dotenv import dotenv_values
import boto3
import pandas as pd
import glob


if __name__ == "__main__":
    env_values = dotenv_values()

    s3 = boto3.client(
        "s3",
        aws_access_key_id=env_values['ACCESS_KEY'],
        aws_secret_access_key=env_values['SECRET_ACCESS_KEY'])

    museum_files = s3.list_objects_v2(Bucket="sigma-resources-museum")

    # Download the historical data files from S3
    for file in museum_files["Contents"]:
        # Get the key of the file
        key = file["Key"]
        # Only download the historical data files that start with "lmnh_"
        if file["Key"].startswith("lmnh_"):
            s3.download_file("sigma-resources-museum",
                             key, f"./files/museum_{key}")

    # Combine the historical data into one csv file
    history_files = glob.glob("./files/museum_lmnh_hist_data_*.csv")
    for file in history_files:
        # Read the csv file and write it to a new csv file without the index
        pd.read_csv(file).to_csv(
            "./files/museum_lmnh_hist_data.csv", index=False)
