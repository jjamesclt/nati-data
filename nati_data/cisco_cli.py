import os
import uuid
import socket
import ipaddress
import pymysql
import configparser
from netmiko import ConnectHandler, NetmikoTimeoutException, NetmikoAuthenticationException

CONFIG_FILE = "nati.ini"
SEEDLIST_FILE = "seedlist.txt"

def load_config():
    config = configparser.ConfigParser()
    config.read(CONFIG_FILE)

    cli_creds = {
        "username": config["ciscocli"]["username"],
        "password": config["ciscocli"]["password"]
    }

    db_config = {
        "host": config["database"]["host"],
        "port": int(config["database"]["port"]),
        "user": config["database"]["username"],
        "password": config["database"]["password"],
        "database": config["database"]["database"],
        "cursorclass": pymysql.cursors.DictCursor
    }

    return cli_creds, db_config

def load_seedlist():
    if not os.path.exists(SEEDLIST_FILE):
        print(f"[!] Seedlist file not found: {SEEDLIST_FILE}")
        return []
    with open(SEEDLIST_FILE, "r") as f:
        return [line.strip() for line in f if line.strip() and not line.startswith("#")]

def resolve_host(seed):
    try:
        ipaddress.ip_address(seed)
        # It's an IP address
        fqdn = socket.getfqdn(seed)
        return seed, fqdn if fqdn and fqdn != seed else None
    except ValueError:
        # It's a hostname/FQDN
        try:
            ip = socket.gethostbyname(seed)
            return ip, seed
        except socket.gaierror:
            print(f"[!] Failed to resolve hostname: {seed}")
            return None, seed

def connect_to_device(ip, username, password):
    device = {
        "device_type": "cisco_ios",
        "host": ip,
        "username": username,
        "password": password,
        "fast_cli": True
    }
    try:
        return ConnectHandler(**device)
    except (NetmikoTimeoutException, NetmikoAuthenticationException) as e:
        print(f"[!] Failed to connect to {ip}: {e}")
        return None

def discover_device_info(conn):
    hostname = conn.send_command("show run | include ^hostname").split("hostname")[-1].strip()
    version_info = conn.send_command("show version")
    model = ""
    version = ""

    for line in version_info.splitlines():
        if "Model number" in line or "Processor board ID" in line:
            model = line.split(":")[-1].strip()
        if "Cisco IOS Software" in line:
            version = line.strip()

    location = None  # Optionally set by user

    return {
        "hostname": hostname,
        "model": model,
        "version": version,
        "location": location
    }

def write_to_db(db_config, device_info, ip, fqdn, device_type="cisco_ios"):
    try:
        conn = pymysql.connect(**db_config)
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM network_device WHERE ip_address = %s", (ip,))
            if cursor.fetchone():
                print(f"[=] Device {ip} already exists in database. Skipping.")
                return

            device_uuid = str(uuid.uuid4())
            cursor.execute("""
                INSERT INTO network_device (
                    device_uuid, hostname, fqdn, ip_address, location, device_type
                ) VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                device_uuid,
                device_info["hostname"],
                fqdn,
                ip,
                device_info["location"],
                device_type
            ))
            conn.commit()
            print(f"[+] Added {device_info['hostname']} ({ip}) to database.")
    except pymysql.MySQLError as err:
        print(f"[!] DB error: {err}")
    finally:
        conn.close()

def main():
    cli_creds, db_config = load_config()
    seed_hosts = load_seedlist()
    if not seed_hosts:
        print("[!] No IPs or hostnames to process.")
        return

    for seed in seed_hosts:
        ip, fqdn = resolve_host(seed)
        if not ip:
            continue

        print(f"[*] Connecting to {ip} (resolved from {seed})...")
        conn = connect_to_device(ip, cli_creds["username"], cli_creds["password"])
        if conn:
            device_info = discover_device_info(conn)
            write_to_db(db_config, device_info, ip, fqdn)
            conn.disconnect()

if __name__ == "__main__":
    main()
