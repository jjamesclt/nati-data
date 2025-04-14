"""
Module for operating with Opengear Lighthouse (v3.7) and Operations Manager (v2.2) devices.

Documentation:
- Lighthouse v3.7:
  https://ftp.opengear.com/download/lighthouse_software/current/documentation/og-rest-api-specification-v3-7.html
- Operations Manager v2.2:
  https://ftp.opengear.com/download/opengear_appliances/OM/archive/19.Q4.0/doc/og-rest-api-specification-v2-2-ngcs.html
"""

import requests
import urllib3

# Disable "InsecureRequestWarning" when skipping TLS verification
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class Lighthouse:
    def __init__(self, base_url, username, password):
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.password = password
        self.session_token = None
        self.session = requests.Session()

    def authenticate(self):
        auth_url = f"https://{self.base_url}/api/v3.7/sessions"
        payload = {
            "username": self.username,
            "password": self.password
        }
        response = self.session.post(auth_url, json=payload, verify=False)
        response.raise_for_status()

        data = response.json()
        if data.get("state") == "authenticated":
            self.session_token = data.get("session")
            self.session.headers.update({"Authorization": "Token " + self.session_token})
            print(f"Authenticated to {self.base_url}")
        else:
            raise Exception("Authentication failed: state != 'authenticated'.")

    def get(self, path, params=None):
        if not self.session_token:
            self.authenticate()
        url = f"https://{self.base_url}{path}"
        response = self.session.get(url, params=params, verify=False)
        response.raise_for_status()
        return response.json()

    def post(self, path, data=None):
        if not self.session_token:
            self.authenticate()
        url = f"https://{self.base_url}{path}"
        response = self.session.post(url, json=data, verify=False)
        response.raise_for_status()
        return response.json()

    def logout(self):
        if self.session_token:
            logout_url = f"https://{self.base_url}/api/v3.7/sessions/self"
            self.session.delete(logout_url, verify=False)
            self.session_token = None
            print(f"Logged out from {self.base_url}")

    def get_nodes(self):
        """Fetch node inventory from Lighthouse."""
        return self.get("/api/v3.7/nodes")
