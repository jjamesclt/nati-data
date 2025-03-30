
import pymysql
import configparser

# Load configuration
config = configparser.ConfigParser()
config.read('nati.ini')

# Database credentials
db_config = {
    'host': config['database']['host'],
    'port': int(config['database']['port']),
    'user': config['database']['username'],
    'password': config['database']['password'],
    'database': config['database']['database']
}

# SQL table creation commands
db_tables = [

"""
CREATE TABLE IF NOT EXISTS site (
    site_uuid CHAR(36) PRIMARY KEY,
    site_id VARCHAR(50) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    country VARCHAR(100) NOT NULL,
    region VARCHAR(100),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX (name),
    INDEX (country),
    INDEX (region)
);
""",

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
    FOREIGN KEY (site_uuid) REFERENCES site(site_uuid) ON DELETE CASCADE,
    INDEX (host),
    INDEX (username)
);
""",

"""
CREATE TABLE IF NOT EXISTS aci_tenant (
    fabric_uuid CHAR(36) NOT NULL,
    tenant_name VARCHAR(100) NOT NULL,
    description VARCHAR(255),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (fabric_uuid, tenant_name),
    FOREIGN KEY (fabric_uuid) REFERENCES aci_fabric(fabric_uuid) ON DELETE CASCADE,
    INDEX (tenant_name)
);
""",

"""
CREATE TABLE IF NOT EXISTS aci_vrf (
    fabric_uuid CHAR(36) NOT NULL,
    tenant_name VARCHAR(100) NOT NULL,
    vrf_name VARCHAR(100) NOT NULL,
    description VARCHAR(255),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (fabric_uuid, tenant_name, vrf_name),
    FOREIGN KEY (fabric_uuid, tenant_name) REFERENCES aci_tenant(fabric_uuid, tenant_name) ON DELETE CASCADE,
    INDEX (vrf_name)
);
""",

"""
CREATE TABLE IF NOT EXISTS aci_bd (
    fabric_uuid CHAR(36) NOT NULL,
    tenant_name VARCHAR(100) NOT NULL,
    bd_name VARCHAR(100) NOT NULL,
    vrf_name VARCHAR(100),
    subnet VARCHAR(50),
    description VARCHAR(255),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (fabric_uuid, tenant_name, bd_name),
    FOREIGN KEY (fabric_uuid, tenant_name) REFERENCES aci_tenant(fabric_uuid, tenant_name) ON DELETE CASCADE,
    FOREIGN KEY (fabric_uuid, tenant_name, vrf_name)
        REFERENCES aci_vrf(fabric_uuid, tenant_name, vrf_name) ON DELETE RESTRICT,
    INDEX (bd_name),
    INDEX (subnet)
);
""",

"""
CREATE TABLE IF NOT EXISTS aci_ap (
    fabric_uuid CHAR(36) NOT NULL,
    tenant_name VARCHAR(100) NOT NULL,
    ap_name VARCHAR(100) NOT NULL,
    description VARCHAR(255),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (fabric_uuid, tenant_name, ap_name),
    FOREIGN KEY (fabric_uuid, tenant_name) REFERENCES aci_tenant(fabric_uuid, tenant_name) ON DELETE CASCADE,
    INDEX (ap_name)
);
""",

"""
CREATE TABLE IF NOT EXISTS aci_epg (
    fabric_uuid CHAR(36) NOT NULL,
    tenant_name VARCHAR(100) NOT NULL,
    ap_name VARCHAR(100) NOT NULL,
    epg_name VARCHAR(100) NOT NULL,
    bd_name VARCHAR(100),
    description VARCHAR(255),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (fabric_uuid, tenant_name, ap_name, epg_name),
    FOREIGN KEY (fabric_uuid, tenant_name, ap_name)
        REFERENCES aci_ap(fabric_uuid, tenant_name, ap_name) ON DELETE CASCADE,
    FOREIGN KEY (fabric_uuid, tenant_name, bd_name)
        REFERENCES aci_bd(fabric_uuid, tenant_name, bd_name) ON DELETE RESTRICT,
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
    for table in db_tables:
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
