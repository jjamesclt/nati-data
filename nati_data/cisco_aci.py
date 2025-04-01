import requests
import pymysql
import configparser
import uuid
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Load configuration
config = configparser.ConfigParser()
config.read('nati.ini')

# Database Credentials
aci_config = {
    'host': config['ciscoaci']['host'],
    'user': config['ciscoaci']['username'],
    'password': config['ciscoaci']['password'],
}

# Database Credentials
db_config = {
    'host': config['database']['host'],
    'port': int(config['database']['port']),
    'user': config['database']['username'],
    'password': config['database']['password'],
    'database': config['database']['database'],
    'cursorclass': pymysql.cursors.DictCursor
}


def get_aci_token():
    aci_host = aci_config['host']
    aci_user = aci_config['user']
    aci_pass = aci_config['password']
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


def insert_aci_node(node, fabric_uuid):
    conn = pymysql.connect(**db_config)
    cursor = conn.cursor()

    insert_query = """
    INSERT INTO aci_node (fabric_uuid, node_id, name, role, serial)
    VALUES (%s, %s, %s, %s, %s)
    ON DUPLICATE KEY UPDATE
    name=VALUES(name), role=VALUES(role), serial=VALUES(serial)
    """

    cursor.execute(insert_query, (fabric_uuid, node['id'], node['name'], node['role'], node['serial']))

    conn.commit()
    cursor.close()
    conn.close()


def collect_aci_nodes():
    aci_host = aci_config['host']
    aci_user = aci_config['user']
    aci_pass = aci_config['password']
    fabrics = get_aci_fabrics()
    for fabric in fabrics:
        token = get_aci_token()
        headers = {"Cookie": f"APIC-cookie={token}"}
        nodes_url = f"https://{aci_host}/api/node/class/fabricNode.json"

        response = requests.get(nodes_url, headers=headers, verify=False)
        response.raise_for_status()
        nodes = response.json()['imdata']

        for node in nodes:
            attr = node['fabricNode']['attributes']
            node_info = {
                'id': attr['dn'],
                'name': attr['name'],
                'role': attr['role'],
                'serial': attr.get('serial', '')
            }
            insert_aci_node(node_info, fabric['fabric_uuid'])

    print("ACI Nodes updated successfully.")


def collect_aci_tenants():
    aci_host = aci_config['host']
    aci_user = aci_config['user']
    aci_pass = aci_config['password']
    fabrics = get_aci_fabrics()
    for fabric in fabrics:
        token = get_aci_token()
        headers = {"Cookie": f"APIC-cookie={token}"}
        tenants_url = f"https://{aci_host}/api/node/class/fvTenant.json"

        response = requests.get(tenants_url, headers=headers, verify=False)
        response.raise_for_status()
        tenants = response.json()['imdata']

        for tenant in tenants:
            attr = tenant['fvTenant']['attributes']
            tenant_info = {
                'id': attr['dn'].split('/')[1],
                'dn': attr['dn'],
                'name': attr['name'],
                'descr': attr.get('descr', '')
            }
            insert_aci_tenant(tenant_info, fabric['fabric_uuid'])

    print("ACI Tenants updated successfully.")


def insert_aci_tenant(tenant, fabric_uuid):
    conn = pymysql.connect(**db_config)
    cursor = conn.cursor()
    insert_query = """
    INSERT INTO aci_tenant (fabric_uuid, tenant_id, tenant_dn, tenant_name, description)
    VALUES (%s, %s, %s, %s, %s)
    ON DUPLICATE KEY UPDATE
    tenant_name=VALUES(tenant_name), description=VALUES(description)
    """
    cursor.execute(insert_query, (fabric_uuid, tenant['id'], tenant['dn'], tenant['name'], tenant['descr']))
    conn.commit()
    cursor.close()
    conn.close()


def insert_aci_vrf(vrf, fabric_uuid):
    conn = pymysql.connect(**db_config)
    cursor = conn.cursor()
    insert_query = """
    INSERT INTO aci_vrf (fabric_uuid, vrf_id, vrf_name, tenant_id, description)
    VALUES (%s, %s, %s, %s, %s)
    ON DUPLICATE KEY UPDATE
    vrf_name=VALUES(vrf_name), description=VALUES(description)
    """
    cursor.execute(insert_query, (fabric_uuid, vrf['id'], vrf['name'], vrf['tenant'], vrf['descr']))
    conn.commit()
    cursor.close()
    conn.close()


def collect_aci_vrfs():
    aci_host = aci_config['host']
    token = get_aci_token()
    headers = {"Cookie": f"APIC-cookie={token}"}
    fabrics = get_aci_fabrics()
    for fabric in fabrics:
        vrf_url = f"https://{aci_host}/api/node/class/fvCtx.json"
        response = requests.get(vrf_url, headers=headers, verify=False)
        response.raise_for_status()
        vrfs = response.json()['imdata']
        for vrf in vrfs:
            attr = vrf['fvCtx']['attributes']
            vrf_info = {
                'id': attr['dn'].split('/')[2],  # extract VRF ID from DN
                'name': attr['name'],
                'tenant': attr['dn'].split('/')[1],  # extract tenant name from DN
                'descr': attr.get('descr', '')
            }
            insert_aci_vrf(vrf_info, fabric['fabric_uuid'])

    print("ACI VRFs updated successfully.")


def insert_aci_ap(ap, fabric_uuid):
    conn = pymysql.connect(**db_config)
    cursor = conn.cursor()
    insert_query = """
    INSERT INTO aci_ap (fabric_uuid, ap_id, ap_name, tenant_id, description)
    VALUES (%s, %s, %s, %s, %s)
    ON DUPLICATE KEY UPDATE
    ap_name=VALUES(ap_name), description=VALUES(description)
    """
    cursor.execute(insert_query, (fabric_uuid, ap['id'], ap['name'], ap['tenant'], ap['descr']))
    conn.commit()
    cursor.close()
    conn.close()


def collect_aci_aps():
    token = get_aci_token()
    headers = {"Cookie": f"APIC-cookie={token}"}
    fabrics = get_aci_fabrics()
    for fabric in fabrics:
        ap_url = f"https://{aci_config['host']}/api/node/class/fvAp.json"
        response = requests.get(ap_url, headers=headers, verify=False)
        response.raise_for_status()
        aps = response.json()['imdata']
        for ap in aps:
            attr = ap['fvAp']['attributes']
            ap_info = {
                'id': attr['dn'].split('/')[2],
                'name': attr['name'],
                'tenant': attr['dn'].split('/')[1],
                'descr': attr.get('descr', '')
            }
            insert_aci_ap(ap_info, fabric['fabric_uuid'])

    print("ACI APs updated successfully.")


def insert_aci_bd(bd, fabric_uuid):
    conn = pymysql.connect(**db_config)
    cursor = conn.cursor()
    insert_query = """
    INSERT INTO aci_bd (fabric_uuid, bd_id, bd_name, tenant_id, description)
    VALUES (%s, %s, %s, %s, %s)
    ON DUPLICATE KEY UPDATE
    bd_name=VALUES(bd_name), description=VALUES(description)
    """
    cursor.execute(insert_query, (fabric_uuid, bd['id'], bd['name'], bd['tenant'], bd['descr']))
    conn.commit()
    cursor.close()
    conn.close()


def collect_aci_bds():
    token = get_aci_token()
    headers = {"Cookie": f"APIC-cookie={token}"}
    fabrics = get_aci_fabrics()
    for fabric in fabrics:
        bd_url = f"https://{aci_config['host']}/api/node/class/fvBD.json"
        response = requests.get(bd_url, headers=headers, verify=False)
        response.raise_for_status()
        bds = response.json()['imdata']
        for bd in bds:
            attr = bd['fvBD']['attributes']
            bd_info = {
                'id': attr['dn'].split('/')[2],
                'name': attr['name'],
                'tenant': attr['dn'].split('/')[1],
                'descr': attr.get('descr', '')
            }
            insert_aci_bd(bd_info, fabric['fabric_uuid'])

    print("ACI BDs updated successfully.")


def insert_aci_epg(epg, fabric_uuid):
    conn = pymysql.connect(**db_config)
    cursor = conn.cursor()
    insert_query = """
    INSERT INTO aci_epg (fabric_uuid, epg_id, epg_name, tenant_id, ap_id, description)
    VALUES (%s, %s, %s, %s, %s, %s)
    ON DUPLICATE KEY UPDATE
    epg_name=VALUES(epg_name), description=VALUES(description)
    """
    cursor.execute(insert_query, (fabric_uuid, epg['id'], epg['name'], epg['tenant'], epg['ap'], epg['descr']))
    conn.commit()
    cursor.close()
    conn.close()


def collect_aci_epgs():
    token = get_aci_token()
    headers = {"Cookie": f"APIC-cookie={token}"}
    fabrics = get_aci_fabrics()
    for fabric in fabrics:
        epg_url = f"https://{aci_config['host']}/api/node/class/fvAEPg.json"
        response = requests.get(epg_url, headers=headers, verify=False)
        response.raise_for_status()
        epgs = response.json()['imdata']
        for epg in epgs:
            attr = epg['fvAEPg']['attributes']
            parts = attr['dn'].split('/')
            epg_info = {
                'id': attr['dn'].split('/')[3],
                'name': attr['name'],
                'tenant': parts[1],
                'ap': parts[2],
                'descr': attr.get('descr', '')
            }
            insert_aci_epg(epg_info, fabric['fabric_uuid'])

    print("ACI EPGs updated successfully.")

    
def main():
    collect_aci_tenants()
    collect_aci_nodes()
    collect_aci_vrfs()
    collect_aci_aps()
    collect_aci_bds()
    collect_aci_epgs()


if __name__ == "__main__":
    main()
