"""
Extract real data from Forio runs by trying different API endpoints.
Vensim models may store data differently than Python models.
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

# Fetch a run
headers = {"Authorization": f"Bearer {token}"}
url = f"https://forio.com/v2/run/{FORIO_ORG}/{FORIO_PROJECT}/;saved=true;trashed=false"
url += "?sort=created&direction=desc&startRecord=0&endRecord=1"

resp = requests.get(url, headers=headers)
runs = resp.json()

if not runs:
    print("No runs found")
    exit(1)

run = runs[0]
run_id = run['id']

print("=" * 70)
print(f"Testing different endpoints for run: {run_id}")
print("=" * 70)

# Try various endpoints and methods
test_cases = [
    # Variables endpoint
    ("GET variables", f"https://api.forio.com/v2/model/run/{run_id}/variables"),
    
    # Operations endpoint (might show available data)
    ("GET operations", f"https://api.forio.com/v2/model/run/{run_id}/operations"),
    
    # Full run data with different bases
    ("GET run (api)", f"https://api.forio.com/v2/model/run/{run_id}"),
    ("GET run (forio)", f"https://forio.com/v2/run/{FORIO_ORG}/{FORIO_PROJECT}/{run_id}"),
    
    # Try with include parameter for common Vensim variables
    ("GET with include", f"https://forio.com/v2/run/{FORIO_ORG}/{FORIO_PROJECT}/{run_id}?include=Time,FINAL_TIME,INITIAL_TIME"),
    
    # Data endpoint
    ("GET data", f"https://api.forio.com/v2/data/run/{run_id}"),
]

for name, endpoint in test_cases:
    print(f"\n{name}:")
    print(f"  URL: {endpoint}")
    
    try:
        resp = requests.get(endpoint, headers=headers)
        print(f"  Status: {resp.status_code}")
        
        if resp.status_code == 200:
            try:
                data = resp.json()
                if isinstance(data, dict):
                    keys = list(data.keys())
                    print(f"  Keys ({len(keys)}): {keys[:10]}")
                    
                    # Look for variable-like data
                    for key in ['variables', 'data', 'results', 'values', 'output']:
                        if key in data:
                            print(f"  ✓ Found '{key}': {type(data[key])}")
                            if isinstance(data[key], dict):
                                var_keys = list(data[key].keys())[:5]
                                print(f"    Sample keys: {var_keys}")
                elif isinstance(data, list):
                    print(f"  Type: list with {len(data)} items")
                else:
                    print(f"  Type: {type(data)}")
            except:
                print(f"  Response (first 200 chars): {resp.text[:200]}")
        elif resp.status_code == 404:
            print(f"  ✗ Not found")
        else:
            print(f"  Error: {resp.text[:100]}")
    except Exception as e:
        print(f"  Exception: {e}")

print("\n" + "=" * 70)
print("Checking run metadata for any embedded data...")
print("=" * 70)
print(json.dumps(run, indent=2, default=str))
