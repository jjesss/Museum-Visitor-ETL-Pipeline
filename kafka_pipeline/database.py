"""Database connection and interaction functions for the Kafka pipeline."""
import os
from os import environ
from psycopg2 import connect
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv(".env"))


def get_db_connection():
    """Get a connection to the PostgreSQL database
    using credentials from .env file."""
    return connect(host=environ["DB_HOST"], dbname="museum",
                   user=environ["DB_USER"], password=environ["DB_PASSWORD"],
                   connect_timeout=5)


def load_interaction(conn, site: int, at: str, button_id: int) -> None:
    """
    Insert single interaction into visitor_interactions table
    """
    with conn.cursor() as cur:
        query = """
            INSERT INTO visitor_interactions (site, at, button_id)
            VALUES (%s, %s, %s);
        """
        values = (site, at, button_id)
        cur.execute(query, values)
        conn.commit()
