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

# SQL commands to create tables
create_site_table = """
CREATE TABLE IF NOT EXISTS site (
    site_uuid CHAR(36) NOT NULL,
    site_id VARCHAR(50) NOT NULL,
    name VARCHAR(100) NOT NULL,
    country VARCHAR(100) NOT NULL,
    region VARCHAR(100),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (site_uuid),
    UNIQUE INDEX (site_id),
    INDEX (name),
    INDEX (country),
    INDEX (region)
);
"""

create_aci_fabric_table = """
CREATE TABLE IF NOT EXISTS aci_fabric (
    fabric_uuid CHAR(36) NOT NULL,
    site_uuid CHAR(36) NOT NULL,
    fabric_name VARCHAR(50) NOT NULL,
    url VARCHAR(255) NOT NULL,
    host VARCHAR(100) NOT NULL,
    username VARCHAR(100) NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (fabric_uuid),
    UNIQUE KEY unique_fabric (site_uuid, fabric_name),
    FOREIGN KEY (site_uuid) REFERENCES site(site_uuid),
    INDEX (host),
    INDEX (username)
);
"""

# Additional ACI tables referencing fabric_uuid
aci_tables = ["""
CREATE TABLE IF NOT EXISTS aci_ap (
    ap_id VARCHAR(100) NOT NULL,
    fabric_uuid CHAR(36) NOT NULL,
    name VARCHAR(100) NOT NULL,
    description VARCHAR(255),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (ap_id, fabric_uuid),
    FOREIGN KEY (fabric_uuid) REFERENCES aci_fabric(fabric_uuid),
    INDEX (name)
);
""",
"""
CREATE TABLE IF NOT EXISTS aci_bd (
    bd_id VARCHAR(100) NOT NULL,
    fabric_uuid CHAR(36) NOT NULL,
    name VARCHAR(100) NOT NULL,
    subnet VARCHAR(50),
    description VARCHAR(255),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (bd_id, fabric_uuid),
    FOREIGN KEY (fabric_uuid) REFERENCES aci_fabric(fabric_uuid),
    INDEX (name),
    INDEX (subnet)
);
""",
"""
CREATE TABLE IF NOT EXISTS aci_epg (
    epg_id VARCHAR(100) NOT NULL,
    fabric_uuid CHAR(36) NOT NULL,
    name VARCHAR(100) NOT NULL,
    description VARCHAR(255),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (epg_id, fabric_uuid),
    FOREIGN KEY (fabric_uuid) REFERENCES aci_fabric(fabric_uuid),
    INDEX (name)
);
""",
"""
CREATE TABLE IF NOT EXISTS aci_vrf (
    vrf_id VARCHAR(100) NOT NULL,
    fabric_uuid CHAR(36) NOT NULL,
    name VARCHAR(100) NOT NULL,
    description VARCHAR(255),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (vrf_id, fabric_uuid),
    FOREIGN KEY (fabric_uuid) REFERENCES aci_fabric(fabric_uuid),
    INDEX (name)
);
""",
"""
CREATE TABLE IF NOT EXISTS aci_tenant (
    tenant_id VARCHAR(100) NOT NULL,
    fabric_uuid CHAR(36) NOT NULL,
    name VARCHAR(100) NOT NULL,
    description VARCHAR(255),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (tenant_id, fabric_uuid),
    FOREIGN KEY (fabric_uuid) REFERENCES aci_fabric(fabric_uuid),
    INDEX (name)
);
""",
"""
CREATE TABLE IF NOT EXISTS aci_node (
    node_id VARCHAR(100) NOT NULL,
    fabric_uuid CHAR(36) NOT NULL,
    name VARCHAR(100) NOT NULL,
    role VARCHAR(50) NOT NULL,
    serial VARCHAR(100),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (node_id, fabric_uuid),
    FOREIGN KEY (fabric_uuid) REFERENCES aci_fabric(fabric_uuid),
    INDEX (name),
    INDEX (role)
);
"""]

# Attempt database connection and table creation
try:
    conn = pymysql.connect(**db_config)
    cursor = conn.cursor()

    cursor.execute(create_site_table)
    cursor.execute(create_aci_fabric_table)

    for table in aci_tables:
        cursor.execute(table)

    conn.commit()
    print("All tables including site, aci_fabric, and additional ACI tables created successfully or already exist.")

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