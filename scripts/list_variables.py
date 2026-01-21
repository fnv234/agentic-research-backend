"""List all variables available in a run."""

import os
import base64
import requests
import json
from dotenv import load_dotenv

load_dotenv()
PUBLIC_KEY = os.getenv("PUBLIC_KEY")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
FORIO_ORG = os.getenv("FORIO_ORG", "mitcams")
FORIO_PROJECT = os.getenv("FORIO_PROJECT", "cyberriskmanagement-ransomeware-2023")

# Get OAuth token
creds = base64.b64encode(f"{PUBLIC_KEY}:{PRIVATE_KEY}".encode()).decode()
headers = {
    "Content-Type": "application/x-www-form-urlencoded",
    "Authorization": f"Basic {creds}"
}
data = {"grant_type": "client_credentials"}
r = requests.post("https://api.forio.com/v2/oauth/token", headers=headers, data=data)
r.raise_for_status()
token = r.json()["access_token"]

# Fetch runs
headers = {"Authorization": f"Bearer {token}"}
url = f"https://forio.com/v2/run/{FORIO_ORG}/{FORIO_PROJECT}/;saved=true;trashed=false"
url += "?sort=created&direction=desc&startRecord=0&endRecord=1"

resp = requests.get(url, headers=headers)
runs = resp.json()

if runs:
    run_id = runs[0]['id']
    print(f"Run ID: {run_id}")
    print(f"Model: {runs[0].get('model')}")
    print()
    
    # Try different variable endpoints
    endpoints = [
        f"https://api.forio.com/v2/model/run/{run_id}/variables",
        f"https://forio.com/v2/run/{FORIO_ORG}/{FORIO_PROJECT}/{run_id}/variables",
        f"https://api.forio.com/v2/run/{FORIO_ORG}/{FORIO_PROJECT}/{run_id}/variables",
        f"https://api.forio.com/v2/model/run/{run_id}",
    ]
    
    for endpoint in endpoints:
        print(f"\nTrying: {endpoint}")
        var_resp = requests.get(endpoint, headers=headers)
        print(f"Status: {var_resp.status_code}")
        if var_resp.status_code == 200:
            try:
                data = var_resp.json()
                if isinstance(data, dict):
                    print(f"Keys: {list(data.keys())[:10]}")
                    if 'variables' in data:
                        print(f"Variables found: {len(data['variables'])} items")
                        print(f"Sample variables: {list(data['variables'].keys())[:5]}")
                else:
                    print(f"Type: {type(data)}")
            except:
                print(f"Response (first 200 chars): {var_resp.text[:200]}")
else:
    print("No runs found")
