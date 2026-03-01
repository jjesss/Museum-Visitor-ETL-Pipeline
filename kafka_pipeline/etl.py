"""Kafka consumer that extracts messages from a Kafka topic, 
validates the data, transforms it into the required format, and loads it into a PostgreSQL database.
"""
from os import environ
import json
import logging
import psycopg2
from confluent_kafka import Consumer
# my imports for helper functions and db connection
from validations import validate_data
from database import get_db_connection, load_interaction

# load .env values into environment variables

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


def create_consumer():
    """Create and configure a Kafka consumer using confluent_kafka library."""
    my_consumer = Consumer(
        {
            "bootstrap.servers": environ["BOOTSTRAP_SERVERS"],
            "security.protocol": environ["SECURITY_PROTOCOL"],
            "sasl.mechanisms": environ["SASL_MECHANISM"],
            "sasl.username": environ["USERNAME"],
            "sasl.password": environ["PASSWORD"],
            "group.id": environ["GROUP"]
        }
    )
    return my_consumer


def parse_json(data: str) -> dict:
    """Parse the JSON string into a dictionary and handle parsing errors."""
    # Parse JSON
    try:
        if isinstance(data, dict):
            return data  # already a dict, no need to parse

        parsed_data = json.loads(data)
    except json.JSONDecodeError:
        raise ValueError("Invalid JSON format")
    return parsed_data


def main():
    """Extract data from Kafka topic, 
    validate it, and log results.
    2 Log files, one for successful processing and one for errors, 
    with timestamps and message details.

    """
    my_consumer = create_consumer()

    # === Set up logging ===
    logger = logging.getLogger("__name__")
    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S")

    success_handler = logging.FileHandler("consumer_success.log")
    success_handler.setLevel(logging.DEBUG)
    success_handler.setFormatter(formatter)
    success_handler.addFilter(lambda record: record.levelno < logging.ERROR)

    error_handler = logging.FileHandler("consumer_error.log")
    error_handler.setLevel(logging.INFO)
    error_handler.setFormatter(formatter)

    logger.addHandler(success_handler)
    logger.addHandler(error_handler)
    logger.addHandler(logging.StreamHandler())  # also log to console

    logger.info("=== Starting Kafka consumer ===")
    # === make connection to db for loading data ===
    try:
        conn = get_db_connection()
    except Exception as e:
        logger.error("Failed to connect to database: %s", e)
        return
    logger.info("=== Connected to database successfully")

    my_consumer.subscribe([environ["TOPIC"]])
    logger.info("=== Subscribed to topic %s", environ["TOPIC"])

    try:
        while True:
            # poll for message with 1 second timeout
            msg = my_consumer.poll(timeout=1.0)

            if msg is None:
                continue
            if msg.error():  # check for Kafka error
                logger.error("Consumer error: %s", msg.error())
                continue

            # process the message
            key = msg.key().decode("utf-8") if msg.key() else None
            value = msg.value().decode("utf-8") if msg.value() else None

            try:
                # === Extract and Validate ===
                # parse JSON
                parsed_value = parse_json(value)
                # validate fields: at, val, site
                validate_data(parsed_value)

                # === Transform ===
                # map val/type to button_id using button_type_mapping
                button_id = get_button_id(parsed_value)

                # === Load ===
                load_interaction(
                    conn, parsed_value["site"], parsed_value["at"], button_id)

                logger.debug(
                    "Successfully inserted message: key=%s, value=%s", key, value)

            except psycopg2.Error as e:
                logger.error(
                    "Database error: %s. Key: %s Raw message: %s", e, key, value)
                break  # exit loop on db error to avoid infinite failures
            except ValueError as e:
                logger.error(
                    "Validation failed: %s. Key: %s Raw message: %s", e, key, value)
                continue  # skip to next message on validation error
    except KeyboardInterrupt:  # allow graceful shutdown on Ctrl+C
        logger.info("Consumer interrupted by user")

    finally:
        logger.info("=== Consumer shutting down")
        if conn:
            conn.close()
        try:
            my_consumer.close()
        except Exception as e:
            logger.debug("=== Error closing consumer: %s", e)


def get_button_id(parsed_value: dict) -> int:
    """ Transform the validated message into the format required for loading into the database.
    This includes mapping the val/type to a button_id using the button_type_mapping.

    INPUT = Message dict with keys: at, val, type, site
    OUTPUT = button_id (int) based on the mapping
    """

    m_val = parsed_value["val"]
    m_type = parsed_value.get("type", None)  # type may be None

    button_id = button_type_mapping.get((m_val, m_type))
    if button_id is None:
        raise ValueError(
            f"Invalid combination of val and type: val={m_val}, type={m_type}")
    return button_id


if __name__ == "__main__":
    main()
