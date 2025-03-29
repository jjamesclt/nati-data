import requests
import pymysql
import configparser
import json

# Load configuration
config = configparser.ConfigParser()
config.read('../nati.ini')

# ACI Credentials
aci_host = config['ciscoaci']['host']
aci_user = config['ciscoaci']['username']
aci_pass = config['ciscoaci']['password']

# Database Credentials
db_config = {
    'host': config['database']['host'],
    'port': int(config['database']['port']),
    'user': config['database']['username'],
    'password': config['database']['password'],
    'database': config['database']['database'],
    'cursorclass': pymysql.cursors.DictCursor
}

# Login to ACI and get authentication token
login_url = f"https://{aci_host}/api/aaaLogin.json"
auth_data = {"aaaUser": {"attributes": {"name": aci_user, "pwd": aci_pass}}}
response = requests.post(login_url, json=auth_data, verify=False)
response.raise_for_status()
token = response.json()['imdata'][0]['aaaLogin']['attributes']['token']
headers = {"Cookie": f"APIC-cookie={token}"}

# Get nodes from ACI
nodes_url = f"https://{aci_host}/api/node/class/fabricNode.json"
response = requests.get(nodes_url, headers=headers, verify=False)
response.raise_for_status()
nodes = response.json()['imdata']

# Prepare nodes dictionary
node_list = []
for node in nodes:
    attr = node['fabricNode']['attributes']
    node_info = {
        'id': attr['id'],
        'name': attr['name'],
        'role': attr['role'],
        'serial': attr.get('serial', '')
    }
    node_list.append(node_info)

# Insert nodes into database
conn = pymysql.connect(**db_config)
cursor = conn.cursor()

insert_query = """
INSERT INTO aci_node (id, name, role, serial)
VALUES (%s, %s, %s, %s)
ON DUPLICATE KEY UPDATE
name=VALUES(name), role=VALUES(role), serial=VALUES(serial)
"""

for node in node_list:
    cursor.execute(insert_query, (node['id'], node['name'], node['role'], node['serial']))

conn.commit()
cursor.close()
conn.close()

print("ACI Nodes updated successfully.")
