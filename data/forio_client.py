"""
Simplified Forio API Client
Focuses on fetching existing runs with proper error handling.
"""

import os
import base64
import requests
from typing import List, Dict, Optional
from dotenv import load_dotenv

load_dotenv()

class ForioClient:
    """Simplified client for fetching Forio simulation runs."""
    
    def __init__(self):
        self.public_key = os.getenv("PUBLIC_KEY")
        self.private_key = os.getenv("PRIVATE_KEY")
        self.org = os.getenv("FORIO_ORG", "mitcams")
        self.project = os.getenv("FORIO_PROJECT", "cyberriskmanagement-ransomeware-2023")
        self.token = None
    
    def is_configured(self) -> bool:
        """Check if credentials are configured."""
        return bool(self.public_key and self.private_key)
    
    def _get_token(self) -> Optional[str]:
        """Get OAuth token from Forio."""
        if not self.is_configured():
            return None
        
        if self.token:
            return self.token
        
        try:
            creds = base64.b64encode(
                f"{self.public_key}:{self.private_key}".encode()
            ).decode()
            
            headers = {
                "Content-Type": "application/x-www-form-urlencoded",
                "Authorization": f"Basic {creds}"
            }
            
            response = requests.post(
                "https://api.forio.com/v2/oauth/token",
                headers=headers,
                data={"grant_type": "client_credentials"},
                timeout=10
            )
            
            if response.status_code == 200:
                self.token = response.json()["access_token"]
                return self.token
            
        except Exception as e:
            print(f"Authentication error: {e}")
        
        return None
    
    def test_connection(self) -> Dict:
        """Test connection and return status."""
        status = {
            'configured': self.is_configured(),
            'authenticated': False,
            'runs_found': 0,
            'has_data': False
        }
        
        if not status['configured']:
            return status
        
        token = self._get_token()
        if not token:
            return status
        
        status['authenticated'] = True
        
        try:
            runs = self.fetch_runs(limit=1)
            status['runs_found'] = len(runs)
            
            if runs:
                run = runs[0]
                status['has_data'] = all(
                    field in run and run[field] is not None
                    for field in ['accumulated_profit', 'compromised_systems', 'systems_availability']
                )
        except:
            pass
        
        return status
    
    def fetch_runs(self, limit: int = 20) -> List[Dict]:
        """
        Fetch saved simulation runs.
        
        Returns runs with metadata. Variables may or may not be present
        depending on Vensim model configuration.
        """
        token = self._get_token()
        if not token:
            return []
        
        try:
            headers = {"Authorization": f"Bearer {token}"}
            url = f"https://forio.com/v2/run/{self.org}/{self.project}/;saved=true;trashed=false"
            url += f"?sort=created&direction=desc&startRecord=0&endRecord={limit}"
            
            response = requests.get(url, headers=headers, timeout=15)
            
            if response.status_code == 200:
                runs = response.json()
                
                for run in runs:
                    self._try_fetch_variables(run, headers)
                
                return runs
            
        except Exception as e:
            print(f"Error fetching runs: {e}")
        
        return []
    
    def _try_fetch_variables(self, run: Dict, headers: Dict):
        """Try to fetch variables for a run (may not exist)."""
        run_id = run.get('id')
        if not run_id:
            return
        
        # Try multiple endpoints
        endpoints = [
            f"https://api.forio.com/v2/model/run/{run_id}/variables",
            f"https://api.forio.com/v2/run/{self.org}/{self.project}/{run_id}/variables"
        ]
        
        for endpoint in endpoints:
            try:
                response = requests.get(endpoint, headers=headers, timeout=5)
                if response.status_code == 200:
                    variables = response.json()
                    if variables:
                        run['variables'] = variables
                        self.process_forio_data(variables, run)
                        return
            except:
                continue
    
    def process_forio_data(self, variables, run):
        """Process Forio data and map to run variables."""
        try:
            for var in ['accumulated_profit', 'compromised_systems', 'systems_availability', 'prevention_budget',
                        'detection_budget', 'response_budget', 'recovery_budget', 'systems_at_risk', 'fraction_to_make_profits',
                        'impact_on_business', 'profits']:
                if var in variables:
                    run[var] = variables[var]

            if 'prevention_budget' in variables:
                run['F1'] = variables.get('prevention_budget')
            if 'detection_budget' in variables:
                run['F2'] = variables.get('detection_budget')
            if 'response_budget' in variables:
                run['F3'] = variables.get('response_budget')
            if 'recovery_budget' in variables:
                run['F4'] = variables.get('recovery_budget')
            return
        except Exception as e:
            print(f"Error processing Forio data: {e}")


if __name__ == '__main__':
    print("=" * 70)
    print("Forio Client Test")
    print("=" * 70)
    
    client = ForioClient()
    
    print("\n1. Configuration:")
    print(f"   Configured: {'✓' if client.is_configured() else '✗'}")
    if client.is_configured():
        print(f"   Org: {client.org}")
        print(f"   Project: {client.project}")
    
    print("\n2. Connection Test:")
    status = client.test_connection()
    print(f"   Configured: {'✓' if status['configured'] else '✗'}")
    print(f"   Authenticated: {'✓' if status['authenticated'] else '✗'}")
    print(f"   Runs Found: {status['runs_found']}")
    print(f"   Has Data: {'✓' if status['has_data'] else '✗'}")
    
    if status['authenticated']:
        print("\n3. Fetching Runs:")
        runs = client.fetch_runs(limit=3)
        print(f"   Fetched: {len(runs)} runs")
        
        if runs:
            print("\n   Sample Run:")
            run = runs[0]
            print(f"   ID: {run.get('id')}")
            print(f"   User: {run.get('user', {}).get('userName', 'Unknown')}")
            print(f"   Created: {run.get('created')}")
            
            has_profit = 'accumulated_profit' in run
            has_compromised = 'compromised_systems' in run
            has_availability = 'systems_availability' in run
            
            print(f"\n   Data Available:")
            print(f"   Profit: {'✓' if has_profit else '✗'}")
            print(f"   Compromised: {'✓' if has_compromised else '✗'}")
            print(f"   Availability: {'✓' if has_availability else '✗'}")
            
            if not (has_profit and has_compromised and has_availability):
                print("\n   Vensim model not saving variables")
                print("   Use manual data entry (python scripts/manual_data_entry.py)")