"""
Manual data entry system for simulation results.
Since Vensim model doesn't save variables, this allows you to:
1. Fetch run metadata from Forio
2. Manually enter results for each run
3. Save to local JSON file
4. Use in dashboard
"""

import os
import sys
import base64
import requests
import json
from datetime import datetime
from dotenv import load_dotenv

# Add parent directory to path to import data modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()
PUBLIC_KEY = os.getenv("PUBLIC_KEY")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
FORIO_ORG = os.getenv("FORIO_ORG", "mitcams")
FORIO_PROJECT = os.getenv("FORIO_PROJECT", "cyberriskmanagement-ransomeware-2023")

def get_forio_token():
    creds = base64.b64encode(f"{PUBLIC_KEY}:{PRIVATE_KEY}".encode()).decode()
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": f"Basic {creds}"
    }
    data = {"grant_type": "client_credentials"}
    r = requests.post("https://api.forio.com/v2/oauth/token", headers=headers, data=data)
    r.raise_for_status()
    return r.json()["access_token"]

def fetch_runs(limit=10):
    token = get_forio_token()
    headers = {"Authorization": f"Bearer {token}"}
    url = f"https://forio.com/v2/run/{FORIO_ORG}/{FORIO_PROJECT}/;saved=true;trashed=false"
    url += f"?sort=created&direction=desc&startRecord=0&endRecord={limit}"
    
    resp = requests.get(url, headers=headers)
    if resp.status_code == 200:
        return resp.json()
    return []

def load_existing_data():
    """Load previously entered data."""
    if os.path.exists('simulation_data.json'):
        with open('simulation_data.json', 'r') as f:
            return json.load(f)
    return {}

def save_data(data):
    """Save data to JSON file."""
    with open('simulation_data.json', 'w') as f:
        json.dump(data, f, indent=2)
    print(f"\nData saved to simulation_data.json")

def enter_data_for_run(run):
    """Interactive data entry for a single run."""
    run_id = run['id']
    user = run.get('user', {}).get('userName', 'Unknown')
    created = run.get('created', 'Unknown')
    
    print(f"\n{'='*70}")
    print(f"Run ID: {run_id}")
    print(f"User: {user}")
    print(f"Created: {created}")
    print(f"{'='*70}")
    
    data = {}
    
    # Settings (from facilitator interface)
    print("\nSimulation Settings:")
    data['simulation_level'] = input("  Simulation level (1 or 2): ").strip() or "1"
    data['attack_type'] = input("  Attack type (other/ransomware): ").strip() or "other"
    data['ransom_policy'] = input("  Ransom policy (pay/not_pay): ").strip() or "not_pay"
    data['run_limit'] = input("  Run limit (1-10 or unlimited): ").strip() or "unlimited"
    
    # Budget allocation (F1-F4 as percentages of IT budget)
    print("\nBudget Allocation (F1-F4 as % of IT budget):")
    print("  F1 = Prevention, F2 = Detection, F3 = Response, F4 = Recovery")
    data['F1'] = float(input("  F1 - Prevention budget (%): ") or "0")
    data['F2'] = float(input("  F2 - Detection budget (%): ") or "0")
    data['F3'] = float(input("  F3 - Response budget (%): ") or "0")
    data['F4'] = float(input("  F4 - Recovery budget (%): ") or "0")
    # Also store with descriptive names for compatibility
    data['prevention_budget'] = data['F1']
    data['detection_budget'] = data['F2']
    data['response_budget'] = data['F3']
    data['recovery_budget'] = data['F4']
    
    # Results/Outcomes - Main outputs
    print("\nSimulation Results - Main Outputs:")
    data['accumulated_profit'] = float(input("  Accumulated profit ($): ") or "0")
    data['compromised_systems'] = int(input("  Compromised systems: ") or "0")
    data['profits'] = float(input("  Profits ($): ") or "0")
    data['systems_availability'] = float(input("  Systems availability (0-1): ") or "1.0")
    
    # Additional outputs
    print("\nSimulation Results - Additional Outputs:")
    data['systems_at_risk'] = float(input("  Systems at risk: ") or "0")
    data['fraction_to_make_profits'] = float(input("  Fraction to make profits (0-1): ") or "0")
    data['impact_on_business'] = float(input("  Impact on business (business disturbance): ") or "0")
    
    # Optional attack metrics
    print("\nOptional Attack Metrics:")
    data['total_attacks'] = int(input("  Total attacks (or press Enter to skip): ") or "0") or None
    data['successful_attacks'] = int(input("  Successful attacks (or press Enter to skip): ") or "0") or None
    
    # Metadata
    data['run_id'] = run_id
    data['user'] = user
    data['created'] = created
    data['group'] = run.get('scope', {}).get('group', 'default')
    data['entered_at'] = datetime.now().isoformat()
    
    return data

def main():
    print("=" * 70)
    print("Manual Data Entry for Forio Simulation Runs")
    print("=" * 70)
    
    # Fetch runs from Forio
    print("\nFetching runs from Forio...")
    runs = fetch_runs(10)
    
    if not runs:
        print("No runs found. Check your Forio connection.")
        return
    
    print(f"Found {len(runs)} runs")
    
    # Load existing data
    existing_data = load_existing_data()
    print(f"Loaded {len(existing_data)} previously entered runs")
    
    # Show runs and let user choose
    print(f"\n{'='*70}")
    print("Available Runs:")
    print(f"{'='*70}")
    
    for i, run in enumerate(runs):
        run_id = run['id']
        user = run.get('user', {}).get('userName', 'Unknown')
        created = run.get('created', 'Unknown')[:10]
        status = "✓ Data entered" if run_id in existing_data else "○ No data"
        print(f"{i+1}. {status} | {user} | {created} | {run_id[:20]}...")
    
    print(f"\n{'='*70}")
    choice = input("\nEnter run number to add/edit data (or 'q' to quit): ").strip()
    
    if choice.lower() == 'q':
        print("Goodbye!")
        return
    
    try:
        idx = int(choice) - 1
        if 0 <= idx < len(runs):
            run = runs[idx]
            run_id = run['id']
            
            # Check if data already exists
            if run_id in existing_data:
                print(f"Data already exists for this run:")
                print(json.dumps(existing_data[run_id], indent=2))
                overwrite = input("Overwrite? (y/n): ").strip().lower()
                if overwrite != 'y':
                    print("Cancelled.")
                    return
            
            # Enter data
            data = enter_data_for_run(run)
            
            # Confirm
            print(f"\n{'='*70}")
            print("Review entered data:")
            print(f"{'='*70}")
            print(json.dumps(data, indent=2))
            
            confirm = input("Save this data? (y/n): ").strip().lower()
            if confirm == 'y':
                existing_data[run_id] = data
                save_data(existing_data)
                
                # Optionally save to Data API
                try:
                    from data.forio_data_api import ForioDataAPI
                    data_api = ForioDataAPI()
                    if data_api.is_configured():
                        save_to_api = input("Also save to Forio Data API? (y/n): ").strip().lower()
                        if save_to_api == 'y':
                            # Use run_id as document ID for consistency
                            saved = data_api.save_simulation_result(data, document_id=run_id)
                            if saved:
                                print("Also saved to Forio Data API")
                except ImportError:
                    pass
                except Exception as e:
                    print(f"Could not save to Data API: {e}")
                
                print("\nData saved successfully!")
                print("\nYou can now use this data in the dashboard.")
                print("Run: python dashboard.py")
            else:
                print("Data not saved.")
        else:
            print("Invalid run number.")
    except ValueError:
        print("Invalid input.")

if __name__ == "__main__":
    main()
