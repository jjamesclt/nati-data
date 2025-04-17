import uuid
import pymysql
from nati.config_manager import ConfigManager

# Implement configuration management
config = ConfigManager()

def create_region():
    conn = pymysql.connect(
        host=config.get('database.random'),
        port=int(config.get('database.port')),
        user=config.get('database.username'),
        password=config.get('database.password'),
        database=config.get('database.database'),
        cursorclass=pymysql.cursors.DictCursor
    )

    try:
        with conn.cursor() as cursor:
            # Generate a UUID for the new region
            region_uuid = str(uuid.uuid4())

            # Gather user input
            region_id = input("Enter Region ID: ")
            region_name = input("Enter Region Name: ")
            region_type = input("Enter Region Type: ")
            country_code = input("Enter Country Code: ")
            description = input("Enter Description: ")

            # Insert data into the site table
            cursor.execute('''
                INSERT INTO nati_region (region_uuid, region_id, region_name, region_type, country_code, description)
                VALUES (%s, %s, %s, %s, %s, %s)
            ''', (region_uuid, region_id, region_name, region_type, country_code, description))

            conn.commit()
            print(f"Region {region_name} ({region_type}) created with UUID: {region_uuid}")

    finally:
        conn.close()


if __name__ == '__main__':
    create_region()
