"""Inspect a single run to see what data is available."""

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
    print("=" * 70)
    print(f"Run Metadata (ID: {run_id}):")
    print("=" * 70)
    print(json.dumps(runs[0], indent=2, default=str))
    
    # Fetch variables for this run
    print("\n" + "=" * 70)
    print("Fetching Variables:")
    print("=" * 70)
    var_url = f"https://api.forio.com/v2/model/run/{run_id}/variables"
    var_resp = requests.get(var_url, headers=headers)
    print(f"Status: {var_resp.status_code}")
    if var_resp.status_code == 200:
        variables = var_resp.json()
        print(f"\nFound {len(variables)} variables")
        print("\nFirst 20 variables:")
        for i, (key, val) in enumerate(list(variables.items())[:20]):
            if isinstance(val, (int, float)):
                print(f"  {key}: {val}")
            elif isinstance(val, list) and len(val) < 5:
                print(f"  {key}: {val}")
            else:
                print(f"  {key}: {type(val).__name__} (length: {len(val) if hasattr(val, '__len__') else 'N/A'})")
    else:
        print(f"Error: {var_resp.text}")
else:
    print("No runs found")
