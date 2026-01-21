"""
Enhanced Forio Data Extractor with Comprehensive Error Handling
and Debugging Capabilities

This improved version addresses common connection issues:
1. Better OAuth error handling
2. More detailed logging
3. Multiple endpoint fallbacks
4. Connection validation
5. Automatic retry logic
"""

import os
import base64
import requests
import json
import time
from typing import List, Dict, Optional, Tuple
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()


class ImprovedForioExtractor:
    """Enhanced Forio API client with robust error handling."""
    
    def __init__(self, public_key=None, private_key=None, org=None, project=None):
        """Initialize with credentials and validate configuration."""
        self.public_key = public_key or os.getenv("PUBLIC_KEY")
        self.private_key = private_key or os.getenv("PRIVATE_KEY")
        self.org = org or os.getenv("FORIO_ORG", "mitcams")
        self.project = project or os.getenv("FORIO_PROJECT", "cyberriskmanagement-ransomeware-2023")
        self.token = None
        self.token_expiry = 0
        
        # Validate credentials
        if not self.public_key or not self.private_key:
            raise ValueError(
                "Missing credentials. Set PUBLIC_KEY and PRIVATE_KEY in .env file or pass as parameters."
            )
        
        logger.info(f"Initialized ForioExtractor for {self.org}/{self.project}")
    
    def _make_request(
        self, 
        method: str, 
        url: str, 
        headers: dict = None, 
        data: dict = None,
        max_retries: int = 3,
        retry_delay: int = 2
    ) -> Tuple[bool, Optional[dict], Optional[str]]:
        """
        Make HTTP request with retry logic.
        
        Returns:
            (success, response_data, error_message)
        """
        for attempt in range(max_retries):
            try:
                if method.upper() == "POST":
                    response = requests.post(url, headers=headers, data=data, timeout=30)
                else:
                    response = requests.get(url, headers=headers, timeout=30)
                
                # Log request details
                logger.debug(f"Request: {method} {url}")
                logger.debug(f"Status: {response.status_code}")
                
                if response.status_code == 200:
                    try:
                        return True, response.json(), None
                    except json.JSONDecodeError:
                        logger.warning(f"Non-JSON response: {response.text[:200]}")
                        return True, {"raw": response.text}, None
                
                elif response.status_code == 401:
                    error = "Authentication failed. Check your PUBLIC_KEY and PRIVATE_KEY."
                    logger.error(error)
                    return False, None, error
                
                elif response.status_code == 403:
                    error = "Access forbidden. Check project permissions."
                    logger.error(error)
                    return False, None, error
                
                elif response.status_code == 404:
                    error = f"Resource not found: {url}"
                    logger.warning(error)
                    return False, None, error
                
                elif response.status_code == 429:
                    # Rate limited - wait longer
                    wait_time = retry_delay * (attempt + 1) * 2
                    logger.warning(f"Rate limited. Waiting {wait_time}s before retry {attempt + 1}/{max_retries}")
                    time.sleep(wait_time)
                    continue
                
                else:
                    error = f"HTTP {response.status_code}: {response.text[:200]}"
                    logger.error(error)
                    
                    if attempt < max_retries - 1:
                        logger.info(f"Retrying in {retry_delay}s... (attempt {attempt + 1}/{max_retries})")
                        time.sleep(retry_delay)
                        continue
                    
                    return False, None, error
            
            except requests.exceptions.Timeout:
                error = f"Request timeout on attempt {attempt + 1}"
                logger.error(error)
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                return False, None, error
            
            except requests.exceptions.ConnectionError as e:
                error = f"Connection error: {str(e)}"
                logger.error(error)
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                return False, None, error
            
            except Exception as e:
                error = f"Unexpected error: {str(e)}"
                logger.exception(error)
                return False, None, error
        
        return False, None, "Max retries exceeded"
    
    def get_access_token(self, force_refresh: bool = False) -> Optional[str]:
        """
        Get OAuth access token with caching and automatic refresh.
        
        Args:
            force_refresh: Force token refresh even if cached token is valid
        
        Returns:
            Access token string or None if authentication fails
        """
        # Check if cached token is still valid
        if not force_refresh and self.token and time.time() < self.token_expiry:
            logger.debug("Using cached token")
            return self.token
        
        logger.info("Requesting new OAuth token...")
        
        try:
            # Encode credentials
            credentials = base64.b64encode(
                f"{self.public_key}:{self.private_key}".encode('utf-8')
            ).decode('utf-8')
            
            # Prepare token request
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Authorization': f'Basic {credentials}'
            }
            payload = {'grant_type': 'client_credentials'}
            
            # Make request
            success, response_data, error = self._make_request(
                'POST',
                'https://api.forio.com/v2/oauth/token',
                headers=headers,
                data=payload
            )
            
            if not success:
                logger.error(f"Token request failed: {error}")
                return None
            
            # Extract token
            self.token = response_data.get('access_token')
            expires_in = response_data.get('expires_in', 3600)  # Default 1 hour
            self.token_expiry = time.time() + expires_in - 60  # Refresh 1 min before expiry
            
            if not self.token:
                logger.error("No access_token in response")
                return None
            
            logger.info("✓ Successfully obtained access token")
            return self.token
        
        except Exception as e:
            logger.exception(f"Token acquisition error: {e}")
            return None
    
    def test_connection(self) -> Dict:
        """
        Comprehensive connection test with diagnostics.
        
        Returns:
            Dictionary with detailed status information
        """
        status = {
            'authenticated': False,
            'token_valid': False,
            'api_accessible': False,
            'runs_found': 0,
            'variables_recorded': False,
            'sample_run': None,
            'errors': [],
            'warnings': []
        }
        
        logger.info("=" * 70)
        logger.info("FORIO CONNECTION DIAGNOSTIC TEST")
        logger.info("=" * 70)
        
        # Test 1: Authentication
        logger.info("\n1. Testing authentication...")
        token = self.get_access_token()
        if not token:
            status['errors'].append("Authentication failed")
            logger.error("✗ Authentication failed")
            return status
        
        status['authenticated'] = True
        status['token_valid'] = True
        logger.info(f"✓ Authentication successful (token: {token[:20]}...)")
        
        # Test 2: API Access
        logger.info("\n2. Testing API access...")
        headers = {'Authorization': f'Bearer {token}'}
        
        # Try to list runs
        url = f"https://forio.com/v2/run/{self.org}/{self.project}/;saved=true;trashed=false"
        url += "?sort=created&direction=desc&startRecord=0&endRecord=1"
        
        success, response_data, error = self._make_request('GET', url, headers=headers)
        
        if not success:
            status['errors'].append(f"API access failed: {error}")
            logger.error(f"✗ API access failed: {error}")
            return status
        
        status['api_accessible'] = True
        
        # Check if we got runs
        runs = response_data if isinstance(response_data, list) else []
        status['runs_found'] = len(runs)
        
        if not runs:
            status['warnings'].append("No saved runs found")
            logger.warning("⚠ No saved runs found")
            logger.info("\nTo create runs:")
            logger.info(f"  1. Visit: https://forio.com/app/{self.org}/{self.project}/")
            logger.info("  2. Complete a simulation")
            logger.info("  3. Save the run")
            return status
        
        logger.info(f"✓ Found {len(runs)} saved run(s)")
        
        # Test 3: Variable Recording
        logger.info("\n3. Checking variable recording...")
        sample_run = runs[0]
        run_id = sample_run.get('id')
        
        status['sample_run'] = {
            'id': run_id,
            'created': sample_run.get('created'),
            'user': sample_run.get('user', {}).get('userName', 'Unknown')
        }
        
        # Check multiple endpoints for variables
        variable_endpoints = [
            f"https://api.forio.com/v2/model/run/{run_id}/variables",
            f"https://api.forio.com/v2/run/{self.org}/{self.project}/{run_id}/variables",
            f"https://forio.com/v2/run/{self.org}/{self.project}/{run_id}?include=variables"
        ]
        
        variables_found = False
        for endpoint in variable_endpoints:
            logger.debug(f"Trying: {endpoint}")
            success, response_data, error = self._make_request('GET', endpoint, headers=headers)
            
            if success and response_data:
                # Check if variables exist
                variables = None
                if isinstance(response_data, dict):
                    variables = response_data.get('variables', {})
                
                if variables:
                    variables_found = True
                    status['variables_recorded'] = True
                    status['sample_run']['variables'] = list(variables.keys())[:10]
                    logger.info(f"✓ Variables found at: {endpoint}")
                    logger.info(f"  Sample variables: {list(variables.keys())[:5]}")
                    break
        
        if not variables_found:
            status['warnings'].append("No variables recorded in runs")
            logger.warning("⚠ No variables found in run")
            logger.info("\nPossible reasons:")
            logger.info("  1. Vensim model not configured to save variables")
            logger.info("  2. Variables saved under different endpoint")
            logger.info("  3. Model hasn't been executed with variable recording enabled")
            logger.info("\nSolutions:")
            logger.info("  1. Configure Vensim model to save target variables")
            logger.info("  2. Use manual data entry: python manual_data_entry.py")
            logger.info("  3. Use mock data for testing: python multi_agent_demo_mock.py")
        
        logger.info("\n" + "=" * 70)
        logger.info("DIAGNOSTIC SUMMARY")
        logger.info("=" * 70)
        logger.info(f"Authentication: {'✓' if status['authenticated'] else '✗'}")
        logger.info(f"API Access: {'✓' if status['api_accessible'] else '✗'}")
        logger.info(f"Runs Found: {status['runs_found']}")
        logger.info(f"Variables Recorded: {'✓' if status['variables_recorded'] else '✗'}")
        
        if status['errors']:
            logger.info(f"\nErrors ({len(status['errors'])}):")
            for error in status['errors']:
                logger.info(f"  ✗ {error}")
        
        if status['warnings']:
            logger.info(f"\nWarnings ({len(status['warnings'])}):")
            for warning in status['warnings']:
                logger.info(f"  ⚠ {warning}")
        
        return status
    
    def fetch_runs_with_variables(
        self,
        variables: List[str],
        model_name: str = None,
        groups: List[str] = None,
        start_record: int = 0,
        end_record: int = 100,
        saved_only: bool = True,
        trashed: bool = False
    ) -> List[Dict]:
        """
        Fetch runs with specified variables (enhanced version).
        
        This method tries multiple strategies to get variable data:
        1. Direct variable inclusion in run query
        2. Separate variable fetch for each run
        3. Alternative endpoints
        """
        logger.info(f"Fetching runs with variables: {variables}")
        
        # Get token
        token = self.get_access_token()
        if not token:
            logger.error("Cannot fetch runs without valid token")
            return []
        
        headers = {'Authorization': f'Bearer {token}'}
        
        # Build query
        if not groups:
            groups = [None]
        
        all_runs = []
        
        for group in groups:
            # Build filter string
            filters = []
            if saved_only:
                filters.append('saved=true')
            filters.append(f'trashed={str(trashed).lower()}')
            if model_name:
                filters.append(f'model={model_name}')
            if group:
                filters.append(f'scope.group={group}')
            
            filter_string = ';'.join(filters)
            
            # Try Strategy 1: Include variables in query
            logger.info(f"Strategy 1: Fetching runs with inline variables (group: {group or 'all'})")
            variables_str = ','.join(variables).replace(',', '%2C')
            url = f'https://forio.com/v2/run/{self.org}/{self.project}/;{filter_string}'
            url += f'?sort=created&direction=desc'
            url += f'&include={variables_str}'
            url += f'&startRecord={start_record}&endRecord={end_record}'
            
            success, response_data, error = self._make_request('GET', url, headers=headers)
            
            if not success:
                logger.warning(f"Strategy 1 failed: {error}")
                continue
            
            runs = response_data if isinstance(response_data, list) else []
            logger.info(f"Fetched {len(runs)} runs")
            
            # Strategy 2: Fetch variables separately if not included
            for run in runs:
                run_id = run.get('id')
                if not run.get('variables') or not run['variables']:
                    logger.debug(f"Strategy 2: Fetching variables separately for run {run_id}")
                    
                    # Try multiple variable endpoints
                    var_endpoints = [
                        f"https://api.forio.com/v2/model/run/{run_id}/variables",
                        f"https://api.forio.com/v2/run/{self.org}/{self.project}/{run_id}/variables"
                    ]
                    
                    for var_url in var_endpoints:
                        success, var_data, error = self._make_request('GET', var_url, headers=headers)
                        if success and var_data:
                            if isinstance(var_data, dict):
                                run['variables'] = var_data.get('variables', var_data)
                            break
                
                # Mark if variables are present
                run['has_variables'] = bool(run.get('variables'))
                
                if group:
                    run['_extracted_group'] = group
            
            all_runs.extend(runs)
        
        logger.info(f"Total runs fetched: {len(all_runs)}")
        logger.info(f"Runs with variables: {sum(1 for r in all_runs if r.get('has_variables'))}")
        
        return all_runs
    
    def save_to_json(self, data: List[Dict], filename: str):
        """Save data to JSON file with error handling."""
        try:
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            logger.info(f"✓ Saved {len(data)} records to {filename}")
            return True
        except Exception as e:
            logger.error(f"Failed to save to {filename}: {e}")
            return False

    def fetch_all_runs_metadata(
        self,
        start_record: int = 0,
        end_record: int = 100
    ) -> List[Dict]:
        """
        Fetch run metadata without variables (faster).
        Matches the legacy ForioDataExtractor interface expected by dashboard.py.
        """
        token = self.get_access_token()
        if not token:
            return []
        headers = {'Authorization': f'Bearer {token}'}
        url = (
            f'https://forio.com/v2/run/{self.org}/{self.project}/;saved=true;trashed=false'
            f'?sort=created&direction=desc&startRecord={start_record}&endRecord={end_record}'
        )
        success, response_data, error = self._make_request('GET', url, headers=headers)
        if not success or not isinstance(response_data, list):
            logger.warning(f"fetch_all_runs_metadata failed: {error}")
            return []
        return response_data

    def extract_variables_from_runs(
        self,
        runs: List[Dict],
        variable_names: List[str]
    ) -> List[Dict]:
        """
        Extract specific variables from run payloads into a flat structure.
        Matches the legacy method used by dashboard.py.
        """
        extracted: List[Dict] = []
        for run in runs:
            run_data = {
                'id': run.get('id'),
                'created': run.get('created'),
                'user': run.get('user', {}).get('userName', 'Unknown'),
                'group': run.get('scope', {}).get('group', run.get('_extracted_group', 'default'))
            }
            variables = run.get('variables', {}) or {}
            for var_name in variable_names:
                run_data[var_name] = variables.get(var_name)
            extracted.append(run_data)
        return extracted


# Standalone test script
if __name__ == '__main__':
    print("\n" + "=" * 70)
    print("IMPROVED FORIO CONNECTION TEST")
    print("=" * 70)
    
    try:
        # Initialize extractor
        extractor = ImprovedForioExtractor()
        
        # Run comprehensive diagnostic
        status = extractor.test_connection()
        
        # If authentication works, try fetching data
        if status['authenticated'] and status['api_accessible']:
            print("\n" + "=" * 70)
            print("ATTEMPTING DATA EXTRACTION")
            print("=" * 70)
            
            variables = [
                'accumulated_profit',
                'compromised_systems',
                'systems_availability',
                'prevention_budget',
                'detection_budget',
                'response_budget'
            ]
            
            runs = extractor.fetch_runs_with_variables(
                variables=variables,
                start_record=0,
                end_record=10
            )
            
            if runs:
                print(f"\n✓ Successfully fetched {len(runs)} runs")
                
                # Show sample run
                sample = runs[0]
                print("\nSample run structure:")
                print(f"  ID: {sample.get('id')}")
                print(f"  Created: {sample.get('created')}")
                print(f"  User: {sample.get('user', {}).get('userName', 'Unknown')}")
                print(f"  Has variables: {sample.get('has_variables', False)}")
                
                if sample.get('variables'):
                    print(f"  Variables present: {list(sample['variables'].keys())[:5]}")
                
                # Save to file
                extractor.save_to_json(runs, 'forio_runs_extracted.json')
            else:
                print("\n✗ No runs fetched")
        
        print("\n" + "=" * 70)
        print("NEXT STEPS")
        print("=" * 70)
        
        if not status['authenticated']:
            print("\n1. Check your .env file:")
            print("   - PUBLIC_KEY=your_key_here")
            print("   - PRIVATE_KEY=your_key_here")
            print("\n2. Verify credentials at: https://forio.com/")
        
        elif status['runs_found'] == 0:
            print("\n1. Create simulation runs:")
            print(f"   - Visit: https://forio.com/app/{extractor.org}/{extractor.project}/")
            print("   - Complete a simulation")
            print("   - Save the run")
        
        elif not status['variables_recorded']:
            print("\n1. Configure Vensim model to save variables")
            print("   OR")
            print("2. Use manual data entry:")
            print("   python manual_data_entry.py")
            print("   OR")
            print("3. Use mock data for testing:")
            print("   python multi_agent_demo_mock.py")
        
        else:
            print("\n✓ Connection fully working!")
            print("\nYou can now:")
            print("  - Run the dashboard: python dashboard.py")
            print("  - Analyze simulations: python multi_agent_demo.py")
    
    except Exception as e:
        logger.exception("Test failed with exception")
        print(f"\n✗ Test failed: {e}")
        print("\nFor support, check:")
        print("  - README.md")
        print("  - SUPERVISOR_SUMMARY.md")
        print("  - Forio docs: https://forio.com/epicenter/docs/")

# Backward-compatible alias so existing imports keep working
# dashboard.py imports ForioDataExtractor
ForioDataExtractor = ImprovedForioExtractor