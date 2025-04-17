import uuid
import pymysql
from nati.config_manager import ConfigManager

# Implement configuration management
config = ConfigManager()

def safe_decimal(val):
    try:
        return float(val)
    except (TypeError, ValueError):
        return None


def create_site():
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
            site_uuid = str(uuid.uuid4())

            # Gather user input
            region_uuid = input("Enter Region UUID: ")
            site_id = input("Enter Site ID: ")
            site_name = input("Enter Site Name: ")
            site_type = input("Enter Site Type: ")
            address = input("Enter Address: ")
            city = input("Enter City: ")
            state = input("Enter State: ")
            postal_code = input("Enter Postal Code: ")
            country = input("Enter Country: ")
            latitude = input("Enter Latitude (decimal): ")
            longitude = input("Enter Longitude (decimal): ")
            description = input("Enter Description: ")

            # Insert data into the site table
            cursor.execute('''
                INSERT INTO nati_site (site_uuid, region_uuid, site_id, site_name, site_type, address, city, state, postal_code,
                country, latitude, longitude, description)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ''', (site_uuid, region_uuid, site_id, site_name, site_type, address, city, state, postal_code,
                    country, safe_decimal(latitude), safe_decimal(longitude), description))

            conn.commit()
            print(f"Site {site_name} ({site_id}) created with UUID: {site_uuid}")

    finally:
        conn.close()

if __name__ == '__main__':
    create_site()
