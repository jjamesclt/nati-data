import os
import sys
import configparser
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import OperationalError

# Read database configuration
config = configparser.ConfigParser()
config.read("nati.ini")

db_type = config["database"]["type"].lower()

if db_type == "sqlite":
    sqlite_file = config["database"]["filename"]

    # Check if the SQLite file exists
    if os.path.exists(sqlite_file):
        print(f"Error: SQLite database file '{sqlite_file}' already exists.")
        print("Please rename or delete the file before running this script.")
        sys.exit(1)

    DATABASE_URL = f"sqlite:///{sqlite_file}"

elif db_type == "mariadb":
    host = config["database"]["host"]
    port = config["database"]["port"]
    database = config["database"]["database"]
    username = config["database"]["username"]
    password = config["database"]["password"]

    DATABASE_URL = f"mysql+pymysql://{username}:{password}@{host}:{port}/{database}"

else:
    print(
        "Error: Unsupported database type. Choose 'sqlite' or 'mariadb' in config.ini."
    )
    sys.exit(1)

# Initialize SQLAlchemy
engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Ensure SQLite enforces foreign keys
if db_type == "sqlite":

    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON;")
        cursor.close()


# Test database connection for MariaDB
if db_type == "mariadb":
    try:
        with engine.connect() as conn:
            print(f"Successfully connected to MariaDB database: {database}")
    except OperationalError as e:
        print(f"Error: Unable to connect to MariaDB database '{database}'.")
        print(
            "Make sure the database exists and your credentials are correct.")
        print(f"Detailed error: {e}")
        sys.exit(1)
