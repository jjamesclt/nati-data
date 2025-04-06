import configparser
import pymysql
import sqlite3

# Load configuration
config = configparser.ConfigParser()
config.read('nati.ini')

# Fetch the database type
db_type = config['database']['type'].lower()

# Common SQL scripts for each DB
db_scripts = {
    'mysql': """
        CREATE TABLE IF NOT EXISTS site (
            site_uuid CHAR(36) PRIMARY KEY,
            site_id VARCHAR(50) NOT NULL UNIQUE,
            name VARCHAR(100) NOT NULL,
            country VARCHAR(2) NOT NULL,
            region VARCHAR(100),
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX (name)
        );
    """,

    'sqlite3': """
        CREATE TABLE IF NOT EXISTS site (
            site_uuid CHAR(36) PRIMARY KEY,
            site_id TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            country TEXT NOT NULL CHECK(length(country) = 2),
            region TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TRIGGER IF NOT EXISTS update_site_timestamp
        AFTER UPDATE ON site
        FOR EACH ROW
        BEGIN
            UPDATE site SET timestamp = CURRENT_TIMESTAMP WHERE site_uuid = old.site_uuid;
        END;

        CREATE INDEX IF NOT EXISTS site_name_idx ON site (name);
    """
}

# Execute the appropriate SQL script based on the database type
if db_type == 'mysql' or db_type == 'mariadb':
    db_config = {
        'host': config['database']['host'],
        'port': int(config['database']['port']),
        'user': config['database']['username'],
        'password': config['database']['password'],
        'database': config['database']['database']
    }
    with pymysql.connect(**db_config) as conn:
        with conn.cursor() as cursor:
            cursor.execute(db_scripts['mysql'])
        conn.commit()
        print("MySQL/MariaDB: Table created successfully.")

elif db_type == 'sqlite3':
    db_path = config['database']['database']
    with sqlite3.connect(db_path) as conn:
        conn.executescript(db_scripts['sqlite3'])
        conn.commit()
    print("SQLite3: Table created successfully.")

else:
    print(f"Unsupported database type: {db_type}")
