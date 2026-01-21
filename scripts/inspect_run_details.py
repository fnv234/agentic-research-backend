"""
Inspect a specific run in detail to see all available data
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

print("=" * 70)
print("🔍 DETAILED RUN INSPECTION")
print("=" * 70)

# Get OAuth token
creds = base64.b64encode(f"{PUBLIC_KEY}:{PRIVATE_KEY}".encode()).decode()
headers = {
    "Content-Type": "application/x-www-form-urlencoded",
    "Authorization": f"Basic {creds}"
}
data = {"grant_type": "client_credentials"}
r = requests.post("https://api.forio.com/v2/oauth/token", headers=headers, data=data)
token = r.json()["access_token"]

# Fetch one run
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

print(f"\n📋 Run ID: {run_id}")
print(f"👤 User: {run.get('user', {}).get('userName', 'Unknown')}")
print(f"📅 Created: {run.get('created', 'Unknown')}")

# Print the ENTIRE run object
print(f"\n📦 COMPLETE RUN OBJECT:")
print("=" * 70)
print(json.dumps(run, indent=2))
print("=" * 70)

# Try to get the full run with all details
print(f"\n🔍 Fetching full run details...")
full_run_url = f"https://api.forio.com/v2/run/{FORIO_ORG}/{FORIO_PROJECT}/{run_id}"
full_resp = requests.get(full_run_url, headers=headers)

if full_resp.status_code == 200:
    full_run = full_resp.json()
    print(f"\n📦 FULL RUN OBJECT:")
    print("=" * 70)
    print(json.dumps(full_run, indent=2))
    print("=" * 70)

# Check the model file
if 'model' in run:
    print(f"\n🎯 Model Information:")
    print(f"   File: {run['model'].get('file', 'Unknown')}")
    print(f"   Type: {run['model'].get('type', 'Unknown')}")

# Try to access the run's state/data
state_url = f"https://api.forio.com/v2/run/{FORIO_ORG}/{FORIO_PROJECT}/{run_id}/state"
state_resp = requests.get(state_url, headers=headers)
print(f"\n🔍 State endpoint: {state_resp.status_code}")
if state_resp.status_code == 200:
    print("State data:")
    print(json.dumps(state_resp.json(), indent=2)[:500])

# Try the data collection endpoint
data_url = f"https://api.forio.com/v2/data/{FORIO_ORG}/{FORIO_PROJECT}/{run_id}"
data_resp = requests.get(data_url, headers=headers)
print(f"\n🔍 Data endpoint: {data_resp.status_code}")
if data_resp.status_code == 200:
    data_result = data_resp.json()
    print(f"Data type: {type(data_result)}")
    if isinstance(data_result, list):
        print(f"Data items: {len(data_result)}")
        if data_result:
            print("First item:")
            print(json.dumps(data_result[0], indent=2))

print("\n" + "=" * 70)
print("💡 WHAT TO LOOK FOR:")
print("=" * 70)
print("1. Any keys that might contain simulation results")
print("2. References to variables, outputs, or results")
print("3. Any nested objects that might have the data")
print("4. Compare this with what you see in the web interface graphs")
print()
