import requests
import pymysql
import configparser
import uuid

# Load configuration
config = configparser.ConfigParser()
config.read('nati.ini')

# Database Credentials
db_config = {
    'host': config['database']['host'],
    'port': int(config['database']['port']),
    'user': config['database']['username'],
    'password': config['database']['password'],
    'database': config['database']['database'],
    'cursorclass': pymysql.cursors.DictCursor
}


def get_aci_token(aci_host, aci_user, aci_pass):
    login_url = f"https://{aci_host}/api/aaaLogin.json"
    auth_data = {"aaaUser": {"attributes": {"name": aci_user, "pwd": aci_pass}}}
    response = requests.post(login_url, json=auth_data, verify=False)
    response.raise_for_status()
    return response.json()['imdata'][0]['aaaLogin']['attributes']['token']


def get_aci_fabrics():
    conn = pymysql.connect(**db_config)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM aci_fabric")
    fabrics = cursor.fetchall()
    cursor.close()
    conn.close()
    return fabrics


def insert_aci_node(node, fabric_id):
    conn = pymysql.connect(**db_config)
    cursor = conn.cursor()

    insert_query = """
    INSERT INTO aci_node (fabric_id, id, name, role, serial)
    VALUES (%s, %s, %s, %s, %s)
    ON DUPLICATE KEY UPDATE
    name=VALUES(name), role=VALUES(role), serial=VALUES(serial)
    """

    cursor.execute(insert_query, (fabric_id, node['id'], node['name'], node['role'], node['serial']))

    conn.commit()
    cursor.close()
    conn.close()


def collect_aci_nodes():
    fabrics = get_aci_fabrics()
    for fabric in fabrics:
        token = get_aci_token(fabric['url'], fabric['username'], fabric['password'])
        headers = {"Cookie": f"APIC-cookie={token}"}
        nodes_url = f"https://{fabric['url']}/api/node/class/fabricNode.json"

        response = requests.get(nodes_url, headers=headers, verify=False)
        response.raise_for_status()
        nodes = response.json()['imdata']

        for node in nodes:
            attr = node['fabricNode']['attributes']
            node_info = {
                'id': attr['id'],
                'name': attr['name'],
                'role': attr['role'],
                'serial': attr.get('serial', '')
            }
            insert_aci_node(node_info, fabric['id'])

    print("ACI Nodes updated successfully.")


def insert_aci_fabric(name, url, username, password):
    conn = pymysql.connect(**db_config)
    cursor = conn.cursor()
    insert_query = """
    INSERT INTO aci_fabric (name, url, username, password)
    VALUES (%s, %s, %s, %s)
    """
    cursor.execute(insert_query, (name, url, username, password))
    conn.commit()
    cursor.close()
    conn.close()
    print(f"ACI Fabric '{name}' added successfully.")


def collect_aci_tenants():
    fabrics = get_aci_fabrics()
    for fabric in fabrics:
        token = get_aci_token(fabric['url'], fabric['username'], fabric['password'])
        headers = {"Cookie": f"APIC-cookie={token}"}
        tenants_url = f"https://{fabric['url']}/api/node/class/fvTenant.json"

        response = requests.get(tenants_url, headers=headers, verify=False)
        response.raise_for_status()
        tenants = response.json()['imdata']

        for tenant in tenants:
            attr = tenant['fvTenant']['attributes']
            tenant_info = {
                'id': attr['dn'],
                'name': attr['name'],
                'descr': attr.get('descr', '')
            }
            insert_aci_tenant(tenant_info, fabric['id'])

    print("ACI Tenants updated successfully.")


def insert_aci_tenant(tenant, fabric_id):
    conn = pymysql.connect(**db_config)
    cursor = conn.cursor()
    insert_query = """
    INSERT INTO aci_tenant (fabric_id, tenant_id, name, description)
    VALUES (%s, %s, %s, %s)
    ON DUPLICATE KEY UPDATE
    name=VALUES(name), description=VALUES(description)
    """
    cursor.execute(insert_query, (fabric_id, tenant['id'], tenant['name'], tenant['descr']))
    conn.commit()
    cursor.close()
    conn.close()


def new_fabric():
    site_uuid = input("Enter Site UUID: ").strip()
    fabric_name = input("Enter Fabric Name: ").strip()
    url = input("Enter URL: ").strip()
    host = input("Enter Host: ").strip()
    username = input("Enter Username: ").strip()

    # Generate a unique fabric UUID
    fabric_uuid = str(uuid.uuid4())

    # Connect to the database
    conn = pymysql.connect(**db_config)
    cursor = conn.cursor()

    # Insert data into the aci_fabric table
    insert_query = """
    INSERT INTO aci_fabric (fabric_uuid, site_uuid, fabric_name, url, host, username)
    VALUES (%s, %s, %s, %s, %s, %s)
    ON DUPLICATE KEY UPDATE
    fabric_name = VALUES(fabric_name),
    url = VALUES(url),
    host = VALUES(host),
    username = VALUES(username)
    """

    cursor.execute(insert_query, (fabric_uuid, site_uuid, fabric_name, url, host, username))
    conn.commit()

    cursor.close()
    conn.close()

    print(f"Fabric created successfully with UUID: {fabric_uuid}")
    
def main():
    new_fabric()

if __name__ == "__main__":
    main()
