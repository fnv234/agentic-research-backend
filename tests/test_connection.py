#!/usr/bin/env python
"""
Quick test script to verify Forio connection and see available data.
Run this first to make sure everything is configured correctly.
"""

import os
import base64
import requests
from dotenv import load_dotenv

load_dotenv()
PUBLIC_KEY = os.getenv("PUBLIC_KEY")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
FORIO_ORG = os.getenv("FORIO_ORG", "mitcams")
FORIO_PROJECT = os.getenv("FORIO_PROJECT", "cyberriskmanagement-ransomeware-2023")

print("=" * 70)
print("🔍 Forio Connection Test")
print("=" * 70)

# Step 1: Check environment variables
print("\n1️⃣  Checking environment variables...")
if not PUBLIC_KEY or not PRIVATE_KEY:
    print("❌ Missing PUBLIC_KEY or PRIVATE_KEY in .env file")
    print("   Please create a .env file with your credentials")
    exit(1)
print(f"✅ PUBLIC_KEY: {PUBLIC_KEY[:10]}...")
print(f"✅ PRIVATE_KEY: {'*' * 10}...")
print(f"✅ Organization: {FORIO_ORG}")
print(f"✅ Project: {FORIO_PROJECT}")

# Step 2: Get OAuth token
print("\n2️⃣  Requesting OAuth token...")
creds = base64.b64encode(f"{PUBLIC_KEY}:{PRIVATE_KEY}".encode()).decode()
headers = {
    "Content-Type": "application/x-www-form-urlencoded",
    "Authorization": f"Basic {creds}"
}
data = {"grant_type": "client_credentials"}

try:
    r = requests.post("https://api.forio.com/v2/oauth/token", headers=headers, data=data)
    r.raise_for_status()
    token = r.json()["access_token"]
    print(f"✅ Token acquired: {token[:20]}...")
except Exception as e:
    print(f"❌ OAuth failed: {e}")
    exit(1)

# Step 3: Fetch runs
print("\n3️⃣  Fetching saved runs...")
headers = {"Authorization": f"Bearer {token}"}
url = f"https://forio.com/v2/run/{FORIO_ORG}/{FORIO_PROJECT}/;saved=true;trashed=false"
url += "?sort=created&direction=desc&startRecord=0&endRecord=5"

try:
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    runs = resp.json()
    
    if not runs:
        print("⚠️  No saved runs found")
        print("\n   To create runs:")
        print(f"   1. Visit: https://forio.com/app/{FORIO_ORG}/{FORIO_PROJECT}/")
        print("   2. Login as: MIT@2025002 (participant) or MIT@2025001 (facilitator)")
        print("   3. Complete a simulation")
        print("   4. Make sure to SAVE the run")
    else:
        print(f"✅ Found {len(runs)} saved runs")
        
        # Show details of first run
        print("\n4️⃣  Sample run details:")
        run = runs[0]
        print(f"   Run ID: {run.get('id', 'N/A')}")
        print(f"   Created: {run.get('created', 'N/A')}")
        print(f"   User: {run.get('user', {}).get('userName', 'N/A')}")
        
        # Show available variables
        if 'variables' in run:
            print(f"\n   Available variables ({len(run['variables'])} total):")
            for key in list(run['variables'].keys())[:10]:  # Show first 10
                val = run['variables'][key]
                if isinstance(val, (int, float)):
                    print(f"      • {key}: {val}")
                elif isinstance(val, str) and len(val) < 50:
                    print(f"      • {key}: {val}")
                else:
                    print(f"      • {key}: {type(val).__name__}")
            if len(run['variables']) > 10:
                print(f"      ... and {len(run['variables']) - 10} more")
        
        # Test fetching specific variables
        print("\n5️⃣  Testing variable fetch...")
        test_vars = ["accumulated_profit", "compromised_systems", "systems_availability"]
        url_with_vars = f"{url}&include={','.join(test_vars)}"
        resp2 = requests.get(url_with_vars, headers=headers)
        if resp2.status_code == 200:
            runs_with_vars = resp2.json()
            if runs_with_vars and 'variables' in runs_with_vars[0]:
                print("✅ Successfully fetched specific variables:")
                for var in test_vars:
                    val = runs_with_vars[0]['variables'].get(var, 'N/A')
                    print(f"      • {var}: {val}")
        
except Exception as e:
    print(f"❌ Failed to fetch runs: {e}")
    exit(1)

print("\n" + "=" * 70)
print("✅ Connection test complete!")
print("\nNext steps:")
print("   • Run: python multi_agent_demo.py")
print("   • See: README.md for full documentation")
print("=" * 70)
