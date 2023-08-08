import sqlite3
import datetime


def setup_database(schema, db_name="span2nodeB.db"):
    # Connect to SQLite3 database
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    # Generate CREATE TABLE statement dynamically based on schema
    columns = ", ".join(
        [f"{col_name} {col_type}" for col_name, col_type in schema.items()]
    )
    create_table_stmt = f"CREATE TABLE IF NOT EXISTS data_table ({columns})"

    # Execute the CREATE TABLE statement
    cursor.execute(create_table_stmt)

    # Close the connection
    conn.close()


def insert_data_to_db(data, db_name="span2nodeB.db"):
    # Define a mapping of Python data types to appropriate types for database
    type_mapping = {
        int: "FLOAT",
        float: "FLOAT",
        str: "STRING",
        bool: "BOOLEAN",
        bytes: "BYTES",
        datetime.datetime: "TIMESTAMP",
    }

    # Connect to SQLite3 database
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    # Check if the table exists
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='data_table'"
    )
    table_exists = cursor.fetchone()

    # If table doesn't exist, create it dynamically based on provided data
    if not table_exists:
        columns_with_types = ", ".join(
            [
                f"{col_name} {type_mapping[type(sample_value)]}"
                for col_name, sample_value in data[0].items()
            ]
        )
        create_table_stmt = f"CREATE TABLE data_table ({columns_with_types})"
        cursor.execute(create_table_stmt)

    # Prepare data for insertion
    columns = ", ".join(data[0].keys())
    placeholders = ", ".join(["?" for _ in data[0]])
    insert_stmt = f"INSERT INTO data_table ({columns}) VALUES ({placeholders})"

    # Insert data into the database
    cursor.executemany(insert_stmt, [tuple(row.values()) for row in data])

    # Commit the changes
    conn.commit()

    # Close the connection
    conn.close()


def get_latest_timestamp(db_name="span2nodeB.db"):
    # Connect to SQLite3 database
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    try:
        # Query to fetch the latest timestamp
        cursor.execute(
            "SELECT TIMESTAMP FROM data_table ORDER BY TIMESTAMP DESC LIMIT 1"
        )
        result = cursor.fetchone()
    except sqlite3.OperationalError:  # Table doesn't exist
        result = None

    # Close the connection
    conn.close()

    # Return the latest timestamp or None if no data exists
    return result[0] if result else None
