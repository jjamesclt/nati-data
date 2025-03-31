import uuid
import pymysql
import configparser

# Read database configuration from nati.ini
config = configparser.ConfigParser()
config.read('nati.ini')

# Database connection settings
db_settings = config['database']


def create_site():
    conn = pymysql.connect(
        host=db_settings['host'],
        port=int(db_settings['port']),
        user=db_settings['username'],
        password=db_settings['password'],
        database=db_settings['database'],
        cursorclass=pymysql.cursors.DictCursor
    )

    try:
        with conn.cursor() as cursor:
            # Generate a UUID for the new site
            site_uuid = str(uuid.uuid4())

            # Gather user input
            site_id = input("Enter Site ID: ")
            name = input("Enter Site Name: ")
            country = input("Enter Country: ")
            region = input("Enter Region: ")

            # Insert data into the site table
            cursor.execute('''
                INSERT INTO site (site_uuid, site_id, name, country, region)
                VALUES (%s, %s, %s, %s, %s)
            ''', (site_uuid, site_id, name, country, region))

            conn.commit()
            print(f"Site '{name}' created with UUID: {site_uuid}")

    finally:
        conn.close()


if __name__ == '__main__':
    create_site()
