"""
Test Forio API Connection
Run this to verify your credentials and connection to Forio
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
print("🔍 FORIO CONNECTION TEST")
print("=" * 70)

# Check if credentials exist
print("\n1️⃣ Checking credentials...")
if not PUBLIC_KEY or not PRIVATE_KEY:
    print("   ❌ FAILED: PUBLIC_KEY or PRIVATE_KEY not set in .env file")
    print("   📝 Please add them to your .env file:")
    print("      PUBLIC_KEY=your_public_key")
    print("      PRIVATE_KEY=your_private_key")
    exit(1)
else:
    print(f"   ✅ PUBLIC_KEY: {PUBLIC_KEY[:10]}...")
    print(f"   ✅ PRIVATE_KEY: ***hidden***")
    print(f"   ✅ FORIO_ORG: {FORIO_ORG}")
    print(f"   ✅ FORIO_PROJECT: {FORIO_PROJECT}")

# Test OAuth token
print("\n2️⃣ Testing OAuth authentication...")
try:
    creds = base64.b64encode(f"{PUBLIC_KEY}:{PRIVATE_KEY}".encode()).decode()
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": f"Basic {creds}"
    }
    data = {"grant_type": "client_credentials"}
    r = requests.post("https://api.forio.com/v2/oauth/token", headers=headers, data=data)
    
    if r.status_code == 200:
        token = r.json()["access_token"]
        print(f"   ✅ Authentication successful!")
        print(f"   🔑 Token: {token[:20]}...")
    else:
        print(f"   ❌ Authentication failed!")
        print(f"   📄 Status: {r.status_code}")
        print(f"   📄 Response: {r.text}")
        exit(1)
except Exception as e:
    print(f"   ❌ Error: {e}")
    exit(1)

# Test fetching runs
print("\n3️⃣ Testing run data access...")
try:
    headers = {"Authorization": f"Bearer {token}"}
    url = f"https://forio.com/v2/run/{FORIO_ORG}/{FORIO_PROJECT}/;saved=true;trashed=false"
    url += "?sort=created&direction=desc&startRecord=0&endRecord=5"
    
    resp = requests.get(url, headers=headers)
    
    if resp.status_code == 200:
        runs = resp.json()
        print(f"   ✅ Successfully fetched runs!")
        print(f"   📊 Found {len(runs)} saved runs")
        
        if runs:
            print("\n4️⃣ Sample run data:")
            run = runs[0]
            print(f"   🆔 Run ID: {run.get('id', 'N/A')}")
            print(f"   📅 Created: {run.get('created', 'N/A')}")
            print(f"   👤 User: {run.get('user', {}).get('userName', 'N/A')}")
            print(f"   📦 Variables recorded: {len(run.get('variables', {}))}")
            
            if run.get('variables'):
                print(f"   📝 Available variables: {list(run['variables'].keys())[:5]}")
            else:
                print(f"   ⚠️  No variables recorded in this run")
                print(f"   💡 The Vensim model may not be configured to save variables")
        else:
            print("   ⚠️  No saved runs found")
    else:
        print(f"   ❌ Failed to fetch runs!")
        print(f"   📄 Status: {resp.status_code}")
        print(f"   📄 Response: {resp.text}")
        exit(1)
except Exception as e:
    print(f"   ❌ Error: {e}")
    exit(1)

print("\n" + "=" * 70)
print("✅ CONNECTION TEST COMPLETE")
print("=" * 70)
print("\n💡 Next steps:")
print("   • If variables are empty, check REAL_DATA_GUIDE.md")
print("   • Run the dashboard: python dashboard.py")
print("   • Visit: http://localhost:5000")
print()
