"""
Forio Data API Client
Handles storing and retrieving simulation results using Forio's Data API.
This allows storing simulation runs with F1-F4 inputs and all outputs in collections.
"""

import os
import json
import requests
from typing import List, Dict, Optional
from dotenv import load_dotenv

load_dotenv()


class ForioDataAPI:
    """Client for Forio Data API to store and retrieve simulation results."""
    
    def __init__(self):
        self.public_key = os.getenv("PUBLIC_KEY")
        self.private_key = os.getenv("PRIVATE_KEY")
        self.org = os.getenv("FORIO_ORG", "mitcams")
        self.project = os.getenv("FORIO_PROJECT", "cyberriskmanagement-ransomeware-2023")
        self.collection_name = os.getenv("DATA_COLLECTION", "simulation-results")
        self.token = None
        self.base_url = "https://api.forio.com/v2/data"
    
    def _get_token(self) -> Optional[str]:
        """Get OAuth access token."""
        if self.token:
            return self.token
        
        if not self.public_key or not self.private_key:
            return None
        
        try:
            import base64
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
    
    def is_configured(self) -> bool:
        """Check if credentials are configured."""
        return bool(self.public_key and self.private_key)
    
    def save_simulation_result(self, result_data: Dict, document_id: Optional[str] = None) -> Optional[Dict]:
        """
        Save a simulation result to the Data API collection.
        
        Args:
            result_data: Dictionary containing simulation inputs (F1-F4) and outputs
            document_id: Optional specific ID for the document. If None, uses POST (auto-generated ID)
        
        Returns:
            Saved document with id and lastModified fields, or None if failed
        """
        token = self._get_token()
        if not token:
            print("Cannot save: No authentication token")
            return None
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        }
        
        clean_data = {k: v for k, v in result_data.items() if v is not None}
        
        if document_id:
            url = f"{self.base_url}/{self.org}/{self.project}/{self.collection_name}/{document_id}"
            method = "PUT"
        else:
            url = f"{self.base_url}/{self.org}/{self.project}/{self.collection_name}"
            method = "POST"
        
        try:
            if method == "PUT":
                response = requests.put(url, headers=headers, json=clean_data, timeout=15)
            else:
                response = requests.post(url, headers=headers, json=clean_data, timeout=15)
            
            if response.status_code in [200, 201]:
                saved_doc = response.json()
                print(f"Saved simulation result: {saved_doc.get('id', 'unknown')}")
                return saved_doc
            else:
                print(f"Failed to save: HTTP {response.status_code}")
                print(f"   Response: {response.text[:200]}")
                return None
                
        except Exception as e:
            print(f"Error saving simulation result: {e}")
            return None
    
    def get_simulation_result(self, document_id: str) -> Optional[Dict]:
        """
        Retrieve a specific simulation result by document ID.
        
        Args:
            document_id: The ID of the document to retrieve
        
        Returns:
            Document data or None if not found
        """
        token = self._get_token()
        if not token:
            return None
        
        headers = {"Authorization": f"Bearer {token}"}
        url = f"{self.base_url}/{self.org}/{self.project}/{self.collection_name}/{document_id}"
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                print(f"Document {document_id} not found")
                return None
            else:
                print(f"Error retrieving document: HTTP {response.status_code}")
                return None
        except Exception as e:
            print(f"Error: {e}")
            return None
    
    def get_all_results(self, include_fields: Optional[List[str]] = None, 
                       exclude_fields: Optional[List[str]] = None,
                       sort_by: Optional[str] = None,
                       direction: str = "desc",
                       limit: Optional[int] = None) -> List[Dict]:
        """
        Retrieve all simulation results from the collection.
        
        Args:
            include_fields: List of fields to include (only these + id will be returned)
            exclude_fields: List of fields to exclude
            sort_by: Field name to sort by (default: lastModified)
            direction: "asc" or "desc" (default: "desc")
            limit: Maximum number of records to return
        
        Returns:
            List of documents
        """
        token = self._get_token()
        if not token:
            return []
        
        headers = {"Authorization": f"Bearer {token}"}
        url = f"{self.base_url}/{self.org}/{self.project}/{self.collection_name}"
        
        params = {}
        if include_fields:
            params['include'] = ','.join(include_fields)
        if exclude_fields:
            params['exclude'] = ','.join(exclude_fields)
        if sort_by:
            params['sort'] = sort_by
            params['direction'] = direction
        
        if limit:
            headers['Range'] = f"records 0-{limit-1}"
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=15)
            
            if response.status_code in [200, 206]:
                results = response.json()
                if isinstance(results, list):
                    return results
                else:
                    return [results] if results else []
            else:
                print(f"Error retrieving results: HTTP {response.status_code}")
                return []
        except Exception as e:
            print(f"Error: {e}")
            return []
    
    def search_results(self, query: Dict, limit: Optional[int] = None) -> List[Dict]:
        """
        Search for simulation results matching specific criteria.
        
        Args:
            query: Dictionary with field names and values to search for
                  Can use comparison operators: {"field": {"$gt": 100}}
                  Can use logical operators: {"$and": [{"field1": "value"}, {"field2": {"$lt": 50}}]}
            limit: Maximum number of results to return
        
        Returns:
            List of matching documents
        """
        token = self._get_token()
        if not token:
            return []
        
        headers = {"Authorization": f"Bearer {token}"}
        url = f"{self.base_url}/{self.org}/{self.project}/{self.collection_name}"
        
        query_str = json.dumps(query)
        params = {'q': query_str}
        
        if limit:
            headers['Range'] = f"records 0-{limit-1}"
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=15)
            
            if response.status_code in [200, 206]:
                results = response.json()
                if isinstance(results, list):
                    return results
                else:
                    return [results] if results else []
            else:
                print(f"Error searching: HTTP {response.status_code}")
                return []
        except Exception as e:
            print(f"Error: {e}")
            return []
    
    def delete_result(self, document_id: str) -> bool:
        """
        Delete a simulation result by document ID.
        
        Args:
            document_id: The ID of the document to delete
        
        Returns:
            True if successful, False otherwise
        """
        token = self._get_token()
        if not token:
            return False
        
        headers = {"Authorization": f"Bearer {token}"}
        url = f"{self.base_url}/{self.org}/{self.project}/{self.collection_name}/{document_id}"
        
        try:
            response = requests.delete(url, headers=headers, timeout=10)
            if response.status_code == 204:
                print(f"Deleted document: {document_id}")
                return True
            else:
                print(f"Failed to delete: HTTP {response.status_code}")
                return False
        except Exception as e:
            print(f"Error: {e}")
            return False
    
    def save_batch_results(self, results: List[Dict]) -> List[Dict]:
        """
        Save multiple simulation results at once using PUT with array.
        
        Args:
            results: List of dictionaries, each must have an 'id' field
        
        Returns:
            List of saved documents
        """
        token = self._get_token()
        if not token:
            return []
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        }
        url = f"{self.base_url}/{self.org}/{self.project}/{self.collection_name}"
        
        for result in results:
            if 'id' not in result:
                result['id'] = f"run_{hash(json.dumps(result, sort_keys=True))}"
        
        try:
            response = requests.put(url, headers=headers, json=results, timeout=30)
            
            if response.status_code in [200, 201]:
                saved_docs = response.json()
                print(f"Saved {len(saved_docs)} simulation results")
                return saved_docs
            else:
                print(f"Failed to save batch: HTTP {response.status_code}")
                print(f"   Response: {response.text[:200]}")
                return []
        except Exception as e:
            print(f"Error saving batch: {e}")
            return []


if __name__ == '__main__':
    print("=" * 70)
    print("Forio Data API Test")
    print("=" * 70)
    
    api = ForioDataAPI()
    
    print("\n1. Configuration:")
    print(f"   Configured: {'Yes' if api.is_configured() else 'No'}")
    if api.is_configured():
        print(f"   Org: {api.org}")
        print(f"   Project: {api.project}")
        print(f"   Collection: {api.collection_name}")
    
    if not api.is_configured():
        print("\nSet PUBLIC_KEY and PRIVATE_KEY in .env file")
        exit(0)
    
    print("\n2. Testing save operation:")
    sample_result = {
        "F1": 30,
        "F2": 30,
        "F3": 25,
        "F4": 15,
        "prevention_budget": 30,
        "detection_budget": 30,
        "response_budget": 25,
        "recovery_budget": 15,
        "accumulated_profit": 1500000,
        "profits": 1200000,
        "compromised_systems": 8,
        "systems_availability": 0.94,
        "systems_at_risk": 12,
        "fraction_to_make_profits": 0.75,
        "impact_on_business": 3.5,
        "strategy_name": "Balanced",
        "timestamp": "2025-01-07T08:00:00Z"
    }
    
    saved = api.save_simulation_result(sample_result)
    if saved:
        doc_id = saved.get('id')
        print(f"   Document ID: {doc_id}")
        
        print("\n3. Testing retrieval:")
        retrieved = api.get_simulation_result(doc_id)
        if retrieved:
            print(f"Retrieved document with {len(retrieved)} fields")
        
        print("\n4. Testing search:")
        search_results = api.search_results({"F1": {"$gte": 25}}, limit=5)
        print(f"   Found {len(search_results)} results with F1 >= 25")
        
        print("\n5. Testing get all:")
        all_results = api.get_all_results(limit=5)
        print(f"   Retrieved {len(all_results)} results")

