"""
Check if simulation results are stored in Forio Data API.
Facilitator projects often store results separately from run variables.
"""

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
headers = {"Authorization": f"Bearer {token}"}

print("=" * 70)
print("Checking Forio Data API for simulation results")
print("=" * 70)

# Try different Data API endpoints
collections = [
    "results",
    "simulation_results", 
    "runs",
    "outcomes",
    "data",
    "settings",
    "configurations",
    "scores",
    "metrics"
]

for collection in collections:
    url = f"https://api.forio.com/v2/data/{FORIO_ORG}/{FORIO_PROJECT}/{collection}"
    
    try:
        resp = requests.get(url, headers=headers)
        print(f"\n{collection}:")
        print(f"  Status: {resp.status_code}")
        
        if resp.status_code == 200:
            data = resp.json()
            if data:
                print(f"  ✓ FOUND DATA!")
                print(f"  Type: {type(data)}")
                if isinstance(data, list):
                    print(f"  Count: {len(data)}")
                    if data:
                        print(f"  Sample: {json.dumps(data[0], indent=4, default=str)[:500]}")
                elif isinstance(data, dict):
                    print(f"  Keys: {list(data.keys())}")
                    print(f"  Sample: {json.dumps(data, indent=4, default=str)[:500]}")
            else:
                print(f"  Empty collection")
        elif resp.status_code == 404:
            print(f"  Not found")
        else:
            print(f"  Error: {resp.text[:100]}")
    except Exception as e:
        print(f"  Exception: {e}")

# Also check if there's a specific run data endpoint
print(f"\n{'='*70}")
print("Checking for run-specific data storage:")
print(f"{'='*70}")

# Get a run ID
url = f"https://forio.com/v2/run/{FORIO_ORG}/{FORIO_PROJECT}/;saved=true;trashed=false?startRecord=0&endRecord=1"
resp = requests.get(url, headers=headers)
runs = resp.json()

if runs:
    run_id = runs[0]['id']
    print(f"\nUsing run ID: {run_id}")
    
    # Try to get data associated with this run
    data_endpoints = [
        f"https://api.forio.com/v2/data/{FORIO_ORG}/{FORIO_PROJECT}/run/{run_id}",
        f"https://api.forio.com/v2/data/{FORIO_ORG}/{FORIO_PROJECT}?q=runId:{run_id}",
        f"https://api.forio.com/v2/data/{FORIO_ORG}/{FORIO_PROJECT}?q=run_id:{run_id}",
    ]
    
    for endpoint in data_endpoints:
        try:
            resp = requests.get(endpoint, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                if data:
                    print(f"\n✓ Found data at: {endpoint}")
                    print(f"  {json.dumps(data, indent=2, default=str)[:500]}")
        except:
            pass

print(f"\n{'='*70}")
print("Summary:")
print(f"{'='*70}")
print("If no data found above, the simulation results are either:")
print("  1. Not being saved (need to configure Vensim model)")
print("  2. Stored in a custom collection name")
print("  3. Only available through the facilitator interface")
print("\nNext step: Contact project admin to ask where results are stored")
