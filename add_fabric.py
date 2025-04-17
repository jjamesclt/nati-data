import uuid
import pymysql
from nati.config_manager import ConfigManager

# Implement configuration management
config = ConfigManager()

def add_fabric():
    conn = pymysql.connect(
        host=config.get('database.random'),
        port=int(config.get('database.port')),
        user=config.get('database.username'),
        password=config.get('database.password'),
        database=config.get('database.database'),
    )

    try:
        with conn.cursor() as cursor:
            # Generate a unique UUID for the fabric
            fabric_uuid = str(uuid.uuid4())


            # Gather user input
            site_uuid = input("Enter Site ID: ").strip()
            fabric_name = input("Enter Fabric Name: ").strip()
            fabric_url = input("Enter URL: ").strip()
            fabric_host = input("Enter Host: ").strip()
            fabric_username = input("Enter Username: ").strip()

            # Insert data into the site table
            cursor.execute('''
                INSERT INTO aci_fabric (fabric_uuid, site_uuid, fabric_name, url, host, username)
                VALUES (%s, %s, %s, %s, %s, %s)
            ''', (fabric_uuid, site_uuid, fabric_name, fabric_url, fabric_host, fabric_username))

            conn.commit()
            print(f"Fabric '{fabric_name}' added with UUID: {fabric_uuid}")

    finally:
        conn.close()


if __name__ == '__main__':
    add_fabric()
