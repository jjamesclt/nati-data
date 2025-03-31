import uuid
import pymysql
import configparser

# Read database configuration from nati.ini
config = configparser.ConfigParser()
config.read('nati.ini')

# Database connection settings
db_settings = config['database']


def add_fabric():
    conn = pymysql.connect(
        host=db_settings['host'],
        port=int(db_settings['port']),
        user=db_settings['username'],
        password=db_settings['password'],
        database=db_settings['database']
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
