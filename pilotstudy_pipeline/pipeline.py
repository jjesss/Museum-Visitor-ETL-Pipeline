"""
ETL Process.
- created db museum: psql museum
- all tables from 3NF ERD created in db using schema.sql: psql museum -f schema.sql
- all the master data seeded into the relevant tables
"""
import os
from dotenv import dotenv_values
from psycopg2 import connect
from psycopg2.extras import execute_values
import pandas as pd
import glob
import json
from datetime import datetime
import logging
import argparse
logger = logging.getLogger(__name__)


def get_db_connection():
    """Get a connection to the PostgreSQL database
    using credentials from .env file."""
    env_values = dotenv_values()
    return connect(host=env_values["DB_HOST"], dbname="museum",
                   user=env_values["DB_USER"], password=env_values["DB_PASSWORD"])


def load_exhibitions(conn, args) -> None:
    """
    Load exhibition data from the exhibition
    json files into the exhibition table.
    """
    exhibition_files = glob.glob(args.exhibition_data_file_path)
    with conn.cursor() as cur:
        for file in exhibition_files:
            try:
                # Extract data
                with open(file) as f:
                    exhibition_data = json.load(f)

                #  Validate data
                if not all([field in exhibition_data for field in
                            ['EXHIBITION_ID', 'EXHIBITION_NAME', 'FLOOR', 'DEPARTMENT', 'START_DATE', 'DESCRIPTION']]):
                    raise ValueError(
                        f"Data validation failed for {file}: Missing required fields")

                # Transform data
                id = int(exhibition_data['EXHIBITION_ID'][-2:])
                name = exhibition_data['EXHIBITION_NAME']
                # floor = exhibition_data['FLOOR'],
                floor = - \
                    1 if exhibition_data['FLOOR'] == 'Vault' else exhibition_data['FLOOR']
                department = exhibition_data['DEPARTMENT']
                try:
                    start_date = datetime.strptime(
                        exhibition_data['START_DATE'], '%d/%m/%y').date()
                except ValueError:
                    raise ValueError(
                        f"Data transformation failed for {file}: Invalid date format")
                description = exhibition_data['DESCRIPTION']

                # Load data
                query = """ 
                            INSERT INTO exhibition (id, name, floor, department, start_date, description)
                            VALUES (%s, %s, %s, %s, %s, %s) 
                            ON CONFLICT (id) DO NOTHING;
                            """
                cur.execute(query, (id, name, floor, department,
                            start_date, description))

            except Exception as e:
                logging.error(
                    f"Failed to load exhibition data from {file}: {e}")
                raise


def load_visitor_interactions(conn: Connection, args: argparse) -> None:
    """
    Load visitor interactions data from the combined historical csv file 
    into the visitor_interactions table.
    """
    # create mapping: (val,type) to determine the button_type_id
    button_type_mapping = {
        (-1, 0): 0,  # assistance
        (-1, 1): 1,  # emergency
        (0, None): 2,  # rating 0
        (1, None): 3,  # rating 1
        (2, None): 4,  # rating 2
        (3, None): 5,  # rating 3
        (4, None): 6,  # rating 4
    }

    # Extract data
    history_data = pd.read_csv(args.hist_data_file_path)

    # Transform data
    history_data["type_val_tuple"] = history_data.apply(lambda row: (row['val'],
                                                                     None if pd.isna(row['type'])
                                                                     else int(row['type'])), axis=1)
    history_data["button_id"] = history_data["type_val_tuple"].map(
        button_type_mapping)

    # Validate data
    if history_data["button_id"].isnull().any():
        raise ValueError("Found unmapped button types")
    if history_data['site'].isna().any():
        raise ValueError(
            "Data validation failed: Missing exhibition site values")
    if history_data['at'].isna().any():
        raise ValueError(
            "Data validation failed: Missing timestamp values")

    # Insert data into visitor_interactions table
    with conn.cursor() as cur:
        query = """
            INSERT INTO visitor_interactions (site, at, button_id)
            VALUES %s
            ON CONFLICT DO NOTHING;
        """
        values = [tuple(row) for row in history_data[['site', 'at',
                                                      'button_id']].values]
        execute_values(cur, query, values)


def call_parser():
    """Gives users the option to specify what they want to load"""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--load_exhibition_data', action='store_true', help='Load exhibition data from JSON files')
    parser.add_argument(
        '--load_hist_data', action='store_true', help='Load historical visitor interactions data from CSV file')
    parser.add_argument(
        '--hist_data_file_path', default='./files/museum_lmnh_hist_data.csv'
    )
    parser.add_argument(
        '--exhibition_data_file_path', default='./files/museum_lmnh_exhibition_*.json'
    )
    args = parser.parse_args()
    return args


def main():
    print("Current directory:", os.getcwd())
    logging.basicConfig(filename='museum_pipeline.log', level=logging.INFO)
    print("Pipeline started. Check museum_pipeline.log for details.")
    logging.info(f"\n ==== date: {datetime.now()} ===")
    logging.info("Pipeline started.")
    args = call_parser()
    conn = None

    try:
        conn = get_db_connection()
        # Load data into tables
        if not args.load_exhibition_data and not args.load_hist_data:
            # Load everything
            args.load_exhibition_data = True
            args.load_hist_data = True

        if args.load_exhibition_data:
            load_exhibitions(conn, args)
        if args.load_hist_data:
            load_visitor_interactions(conn, args)

        conn.commit()
        logging.info("Pipeline completed successfully.")
    except Exception as e:
        logging.error(f"Pipeline failed: {e}")
        if conn:
            conn.rollback()  # Undo everything
        raise e
    finally:
        if conn:
            conn.close()

    logging.info("Pipeline Ended.")


if __name__ == "__main__":
    main()
