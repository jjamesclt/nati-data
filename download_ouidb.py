import requests
import pymysql
from nati.utils import normalize_mac_prefix
from nati.config_manager import ConfigManager

def download_and_update_ouidb():
    config = ConfigManager()

    if not config.get('network.ouidb_jsondl'):
        print("MAC OUI download is disabled by configuration.")
        return

    download_url = config.get('network.ouidb_jsondl')
    response = requests.get(download_url)

    if not response.ok:
        print(f"Failed to download OUI database: {response.status_code} {response.text}")
        return

    json_data = response.json()

    db_config = {
        'host': config.get('database.host'),
        'port': int(config.get('database.port')),
        'user': config.get('database.username'),
        'password': config.get('database.password'),
        'database': config.get('database.database'),
    }

    conn = pymysql.connect(**db_config)
    cursor = conn.cursor()

    for entry in json_data:
        mac_prefix_raw = entry.get('macPrefix', '')
        vendor_name = entry.get('vendorName', '')

        if not mac_prefix_raw or not vendor_name:
            continue  # Skip incomplete records

        mac_prefix = normalize_mac_prefix(mac_prefix_raw)

        cursor.execute("""
            REPLACE INTO network_ouidb (mac_prefix, vendor_name)
            VALUES (%s, %s)
        """, (mac_prefix, vendor_name))

    conn.commit()
    cursor.close()
    conn.close()

    print(f"Updated {len(json_data)} OUI records successfully.")

if __name__ == "__main__":
    download_and_update_ouidb()
