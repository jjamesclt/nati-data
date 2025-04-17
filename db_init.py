import pymysql
import getpass
from nati.config_manager import ConfigManager

# Database credentials
config = ConfigManager()
default_config = {
    'host': config.get("database.random"),
    'port': int(config.get("database.port")),
    'user': config.get("database.username"),
    'password': config.get("database.password"),
    'database': config.get("database.database")
}

print(default_config["host"])

# Prompt user for elevated credentials
print("Press Enter to use default credentials from nati.ini.")
custom_user = input("Enter high-privilege DB username (or press Enter to use default): ").strip()

if custom_user:
    custom_password = getpass.getpass("Enter password for the high-privilege user: ")
    db_config = {
        'host': default_config['host'],
        'port': default_config['port'],
        'user': custom_user,
        'password': custom_password,
        'database': default_config['database']
    }
else:
    db_config = default_config

# SQL table creation commands - core NATI module
nati_tables = [
"""
CREATE TABLE IF NOT EXISTS nati_region (
    region_uuid CHAR(36) PRIMARY KEY,
    region_id VARCHAR(20) UNIQUE,
    region_name VARCHAR(100) NOT NULL UNIQUE,
    region_type ENUM('physical', 'cloud', 'logical') DEFAULT 'physical',
    country_code CHAR(2),
    description TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
""",
"""
CREATE TABLE IF NOT EXISTS nati_site (
    site_uuid CHAR(36) PRIMARY KEY,
    region_uuid CHAR(36) NOT NULL,
    site_id VARCHAR(20) UNIQUE,
    site_name VARCHAR(150) NOT NULL,
    site_type ENUM('data_center', 'branch', 'lab', 'cloud', 'colo', 'virtual') DEFAULT 'data_center',
    address VARCHAR(255),
    city VARCHAR(100),
    state VARCHAR(50),
    postal_code VARCHAR(20),
    country VARCHAR(100),
    latitude DECIMAL(10,7),
    longitude DECIMAL(10,7),
    description TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (region_uuid) REFERENCES nati_region(region_uuid)
);
""",
"""
CREATE TABLE IF NOT EXISTS nati_location (
    location_uuid CHAR(36) PRIMARY KEY,
    location_id VARCHAR(20) UNIQUE,
    location_name VARCHAR(150) NOT NULL,
    location_type ENUM(
        'rack', 'room', 'floor', 'vpc', 'az',
        'namespace', 'k8s_cluster', 'segment',
        'logical', 'other'
    ) DEFAULT 'rack',
    description TEXT,
    virtual BOOLEAN DEFAULT FALSE,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
""",
"""
CREATE TABLE IF NOT EXISTS nati_location_site_map (
    location_uuid CHAR(36),
    site_uuid CHAR(36),
    PRIMARY KEY (location_uuid, site_uuid),
    FOREIGN KEY (location_uuid) REFERENCES nati_location(location_uuid) ON DELETE CASCADE,
    FOREIGN KEY (site_uuid) REFERENCES nati_site(site_uuid) ON DELETE CASCADE
);
""",
"""
CREATE TABLE IF NOT EXISTS nati_config (
    config_module VARCHAR(100) NOT NULL,
    config_key VARCHAR(100) NOT NULL,
    config_value TEXT NOT NULL,
    PRIMARY KEY (config_module, config_key)
);
""",
"""
CREATE TABLE IF NOT EXISTS nati_user (
    user_uuid CHAR(36) PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    full_name VARCHAR(150),
    email VARCHAR(150),
    active BOOLEAN DEFAULT TRUE,
    source VARCHAR(50) DEFAULT 'local',
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX (username),
    INDEX (email)
);
""",
"""
CREATE TABLE IF NOT EXISTS nati_role (
    role_uuid CHAR(36) PRIMARY KEY,
    role_name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX (role_name)
);
""",
"""
CREATE TABLE IF NOT EXISTS nati_user_role (
    user_uuid CHAR(36) NOT NULL,
    role_uuid CHAR(36) NOT NULL,
    assigned_by VARCHAR(100),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (user_uuid, role_uuid),
    FOREIGN KEY (user_uuid) REFERENCES nati_user(user_uuid) ON DELETE CASCADE,
    FOREIGN KEY (role_uuid) REFERENCES nati_role(role_uuid) ON DELETE CASCADE
);
""",
"""
CREATE TABLE IF NOT EXISTS nati_credential (
    cred_uuid CHAR(36) PRIMARY KEY,
    username TEXT NOT NULL,
    password TEXT NOT NULL,
    description TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""
]

# SQL table creation commands - network module
network_tables = [
"""
CREATE TABLE IF NOT EXISTS network_device (
    device_uuid CHAR(36) PRIMARY KEY,
    hostname VARCHAR(100) NOT NULL,
    fqdn VARCHAR(255),
    ip_address VARCHAR(45),
    location VARCHAR(100),
    device_type VARCHAR(50),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX (hostname),
    INDEX (fqdn),
    INDEX (ip_address)
);
""",
"""
CREATE TABLE IF NOT EXISTS network_interface (
    interface_uuid CHAR(36) PRIMARY KEY,
    device_uuid CHAR(36) NOT NULL,
    interface_id VARCHAR(100) NOT NULL,
    name VARCHAR(100) NOT NULL,
    description VARCHAR(255),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (device_uuid) REFERENCES network_device(device_uuid) ON DELETE CASCADE,
    UNIQUE (device_uuid, interface_id),
    INDEX (name)
);
""",
"""
CREATE TABLE IF NOT EXISTS network_circuit (
    circuit_uuid CHAR(36) PRIMARY KEY,
    interface_uuid CHAR(36) NOT NULL,
    circuit_id VARCHAR(100) NOT NULL UNIQUE,
    provider VARCHAR(100),
    bandwidth VARCHAR(50),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (interface_uuid) REFERENCES network_interface(interface_uuid) ON DELETE CASCADE,
    INDEX (provider)
);
"""
]

# SQL table creation commands - Cisco ACI module
aci_tables = [
"""
CREATE TABLE IF NOT EXISTS aci_fabric (
    fabric_uuid CHAR(36) PRIMARY KEY,
    site_uuid CHAR(36) NOT NULL,
    fabric_name VARCHAR(50) NOT NULL,
    url VARCHAR(255) NOT NULL,
    host VARCHAR(100) NOT NULL,
    username VARCHAR(100) NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE (site_uuid, fabric_name),
    FOREIGN KEY (site_uuid) REFERENCES nati_site(site_uuid) ON DELETE CASCADE
);
""",
"""
CREATE TABLE IF NOT EXISTS aci_tenant (
    fabric_uuid CHAR(36) NOT NULL,
    tenant_dn VARCHAR(100) NOT NULL,
    tenant_id VARCHAR(100) NOT NULL,
    tenant_name VARCHAR(100) NOT NULL,
    description VARCHAR(255),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (fabric_uuid, tenant_id),
    FOREIGN KEY (fabric_uuid) REFERENCES aci_fabric(fabric_uuid) ON DELETE CASCADE
);
""",
"""
CREATE TABLE IF NOT EXISTS aci_vrf (
    fabric_uuid CHAR(36) NOT NULL,
    tenant_id VARCHAR(100) NOT NULL,
    vrf_id VARCHAR(100) NOT NULL,
    vrf_name VARCHAR(100) NOT NULL,
    description VARCHAR(255),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (fabric_uuid, tenant_id, vrf_id),
    FOREIGN KEY (fabric_uuid, tenant_id) REFERENCES aci_tenant(fabric_uuid, tenant_id) ON DELETE CASCADE,
    INDEX (vrf_name)
);
""",
"""
CREATE TABLE IF NOT EXISTS aci_bd (
    fabric_uuid CHAR(36) NOT NULL,
    tenant_id VARCHAR(100) NOT NULL,
    bd_id VARCHAR(100) NOT NULL,
    bd_name VARCHAR(100) NOT NULL,
    vrf_id VARCHAR(100),
    subnet VARCHAR(50),
    description VARCHAR(255),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (fabric_uuid, tenant_id, bd_id),
    FOREIGN KEY (fabric_uuid, tenant_id) REFERENCES aci_tenant(fabric_uuid, tenant_id) ON DELETE CASCADE,
    FOREIGN KEY (fabric_uuid, tenant_id, vrf_id)
        REFERENCES aci_vrf(fabric_uuid, tenant_id, vrf_id) ON DELETE RESTRICT,
    INDEX (bd_name),
    INDEX (subnet)
);
""",
"""
CREATE TABLE IF NOT EXISTS aci_ap (
    fabric_uuid CHAR(36) NOT NULL,
    tenant_id VARCHAR(100) NOT NULL,
    ap_id VARCHAR(100) NOT NULL,
    ap_name VARCHAR(100) NOT NULL,
    description VARCHAR(255),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (fabric_uuid, tenant_id, ap_id),
    FOREIGN KEY (fabric_uuid, tenant_id) REFERENCES aci_tenant(fabric_uuid, tenant_id) ON DELETE CASCADE,
    INDEX (ap_name)
);
""",
"""
CREATE TABLE IF NOT EXISTS aci_epg (
    fabric_uuid CHAR(36) NOT NULL,
    tenant_id VARCHAR(100) NOT NULL,
    ap_id VARCHAR(100) NOT NULL,
    epg_id VARCHAR(100) NOT NULL,
    epg_name VARCHAR(100) NOT NULL,
    description VARCHAR(255),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (fabric_uuid, tenant_id, ap_id, epg_id),
    FOREIGN KEY (fabric_uuid, tenant_id, ap_id)
        REFERENCES aci_ap(fabric_uuid, tenant_id, ap_id) ON DELETE CASCADE,
    INDEX (epg_name)
);
""",
"""
CREATE TABLE IF NOT EXISTS aci_node (
    fabric_uuid CHAR(36) NOT NULL,
    node_id VARCHAR(100) NOT NULL,
    name VARCHAR(100) NOT NULL,
    role VARCHAR(50) NOT NULL,
    serial VARCHAR(100),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (fabric_uuid, node_id),
    FOREIGN KEY (fabric_uuid) REFERENCES aci_fabric(fabric_uuid) ON DELETE CASCADE,
    INDEX (name),
    INDEX (role)
);
"""
]

# Execute SQL
try:
    conn = pymysql.connect(**db_config)
    cursor = conn.cursor()
    for table in nati_tables:
        cursor.execute(table)
    for table in network_tables:
        cursor.execute(table)
    for table in aci_tables:
        cursor.execute(table)
    conn.commit()
    print("All tables created successfully or already exist.")

except pymysql.err.OperationalError as e:
    if '1049' in str(e):
        print("Error: The specified database does not exist. Please create it first.")
    elif '1045' in str(e):
        print("Error: Access denied. Please check your database username and password.")
    else:
        print(f"Operational error: {e}")

except Exception as e:
    print(f"An unexpected error occurred: {e}")

finally:
    if 'conn' in locals() and conn.open:
        cursor.close()
        conn.close()
