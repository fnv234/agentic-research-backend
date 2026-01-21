"""
Unified Data Loader - Handles real CSV data and simulated runs
"""

import os
import csv
import json
from typing import List, Dict, Optional
from datetime import datetime


def load_csv_data(filepath: str = "data/sim_data.csv") -> List[Dict]:
    """Load real simulation data from CSV file."""
    runs = []
    
    if not os.path.exists(filepath):
        print(f"Warning: {filepath} not found")
        return runs
    
    try:
        with open(filepath, 'r') as f:
            reader = csv.DictReader(f)
            for idx, row in enumerate(reader):
                # Convert string values to appropriate types
                run = {
                    'id': f"real_{idx+1}",
                    'source': 'real_data',
                    'timestamp': row.get('timestamp', datetime.now().isoformat()),
                }
                
                # Convert numeric fields
                for key, value in row.items():
                    if key == 'timestamp':
                        continue
                    try:
                        # Try to convert to float
                        if '.' in value:
                            run[key] = float(value)
                        else:
                            run[key] = int(value)
                    except (ValueError, AttributeError):
                        # Keep as string if conversion fails
                        run[key] = value
                
                runs.append(run)
        
        print(f"✓ Loaded {len(runs)} runs from {filepath}")
        
    except Exception as e:
        print(f"Error loading CSV data: {e}")
    
    return runs


def load_manual_data(data_dir: str = "data") -> List[Dict]:
    """Load manually entered simulation runs from JSON files."""
    runs = []
    
    if not os.path.exists(data_dir):
        return runs
    
    # Look for JSON files in the data directory
    for filename in os.listdir(data_dir):
        if filename.startswith('run_') and filename.endswith('.json'):
            filepath = os.path.join(data_dir, filename)
            try:
                with open(filepath, 'r') as f:
                    run_data = json.load(f)
                    run_data['source'] = 'manual'
                    runs.append(run_data)
            except Exception as e:
                print(f"Warning: Could not load {filepath}: {e}")
    
    if runs:
        print(f"✓ Loaded {len(runs)} manual runs")
    
    return runs


def generate_mock_data(count: int = 10) -> List[Dict]:
    """Generate mock simulation data for testing."""
    import random
    
    runs = []
    for i in range(count):
        run = {
            'id': f"mock_{i+1}",
            'source': 'mock',
            'timestamp': datetime.now().isoformat(),
            'accumulated_profit': random.randint(800000, 2000000),
            'compromised_systems': random.randint(0, 25),
            'systems_availability': round(random.uniform(0.85, 0.99), 3),
            'security_investment': random.randint(100000, 500000),
            'recovery_cost': random.randint(50000, 300000),
        }
        runs.append(run)
    
    return runs


def load_runs(prefer_source: Optional[str] = None, limit: Optional[int] = None) -> List[Dict]:
    """
    Load simulation runs from best available source.
    
    Priority:
    1. Real CSV data (sim_data.csv)
    2. Manual JSON data
    3. Mock data
    
    Args:
        prefer_source: Force a specific source ('csv', 'manual', 'mock')
        limit: Maximum number of runs to return
    
    Returns:
        List of run dictionaries
    """
    runs = []
    
    if prefer_source == 'csv' or prefer_source is None:
        csv_runs = load_csv_data()
        if csv_runs:
            runs.extend(csv_runs)
    
    if prefer_source == 'manual' or (prefer_source is None and not runs):
        manual_runs = load_manual_data()
        if manual_runs:
            runs.extend(manual_runs)
    
    if prefer_source == 'mock' or (prefer_source is None and not runs):
        mock_runs = generate_mock_data()
        runs.extend(mock_runs)
    
    # Apply limit if specified
    if limit and len(runs) > limit:
        runs = runs[:limit]
    
    return runs


def get_data_source_info() -> Dict:
    """Get information about available data sources."""
    csv_path = "data/sim_data.csv"
    data_dir = "data"
    
    csv_available = os.path.exists(csv_path)
    csv_count = 0
    if csv_available:
        try:
            with open(csv_path, 'r') as f:
                csv_count = sum(1 for _ in csv.DictReader(f))
        except:
            csv_count = 0
    
    manual_files = []
    manual_count = 0
    if os.path.exists(data_dir):
        manual_files = [f for f in os.listdir(data_dir) 
                       if f.startswith('run_') and f.endswith('.json')]
        manual_count = len(manual_files)
    
    return {
        'csv': {
            'available': csv_available,
            'path': csv_path,
            'count': csv_count
        },
        'manual': {
            'available': manual_count > 0,
            'files': manual_files,
            'count': manual_count
        },
        'mock': {
            'available': True,
            'count': 10
        }
    }


def compare_runs(real_runs: List[Dict], simulated_runs: List[Dict]) -> Dict:
    """
    Compare real data against simulated runs.
    
    Args:
        real_runs: List of real simulation runs
        simulated_runs: List of bot-generated simulated runs
    
    Returns:
        Comparison statistics
    """
    if not real_runs or not simulated_runs:
        return {'error': 'Need both real and simulated runs for comparison'}
    
    # Get common metrics
    real_metrics = real_runs[0].keys()
    sim_metrics = simulated_runs[0].keys()
    common_metrics = set(real_metrics) & set(sim_metrics)
    
    # Remove non-numeric fields
    exclude = {'id', 'source', 'timestamp'}
    numeric_metrics = [m for m in common_metrics if m not in exclude]
    
    comparison = {
        'metrics': {},
        'summary': {}
    }
    
    for metric in numeric_metrics:
        # Calculate statistics for real data
        real_values = [r.get(metric, 0) for r in real_runs if isinstance(r.get(metric), (int, float))]
        sim_values = [s.get(metric, 0) for s in simulated_runs if isinstance(s.get(metric), (int, float))]
        
        if not real_values or not sim_values:
            continue
        
        real_avg = sum(real_values) / len(real_values)
        sim_avg = sum(sim_values) / len(sim_values)
        
        real_min = min(real_values)
        real_max = max(real_values)
        sim_min = min(sim_values)
        sim_max = max(sim_values)
        
        difference = sim_avg - real_avg
        percent_diff = (difference / real_avg * 100) if real_avg != 0 else 0
        
        comparison['metrics'][metric] = {
            'real': {
                'avg': real_avg,
                'min': real_min,
                'max': real_max,
                'count': len(real_values)
            },
            'simulated': {
                'avg': sim_avg,
                'min': sim_min,
                'max': sim_max,
                'count': len(sim_values)
            },
            'difference': difference,
            'percent_difference': percent_diff
        }
    
    # Generate summary insights
    comparison['summary'] = {
        'total_real_runs': len(real_runs),
        'total_simulated_runs': len(simulated_runs),
        'metrics_compared': len(comparison['metrics']),
        'timestamp': datetime.now().isoformat()
    }
    
    return comparison


if __name__ == '__main__':
    print("=" * 70)
    print("Data Loader Test")
    print("=" * 70)
    
    # Test loading from all sources
    print("\n📊 Testing Data Sources:")
    
    csv_runs = load_csv_data()
    print(f"\n  CSV Data: {len(csv_runs)} runs")
    if csv_runs:
        print(f"    Sample: {list(csv_runs[0].keys())}")
    
    manual_runs = load_manual_data()
    print(f"\n  Manual Data: {len(manual_runs)} runs")
    
    mock_runs = generate_mock_data(5)
    print(f"\n  Mock Data: {len(mock_runs)} runs")
    
    # Test unified loader
    print("\n🔄 Testing Unified Loader:")
    all_runs = load_runs()
    print(f"  Total runs loaded: {len(all_runs)}")
    
    # Test data source info
    print("\n📋 Data Source Info:")
    info = get_data_source_info()
    for source, details in info.items():
        print(f"\n  {source.upper()}:")
        for key, value in details.items():
            print(f"    {key}: {value}")
    
    # Test comparison if we have both real and simulated data
    if csv_runs and mock_runs:
        print("\n📊 Testing Comparison:")
        comparison = compare_runs(csv_runs[:5], mock_runs[:5])
        if 'error' not in comparison:
            print(f"  Metrics compared: {comparison['summary']['metrics_compared']}")
            for metric, data in list(comparison['metrics'].items())[:2]:
                print(f"\n  {metric}:")
                print(f"    Real avg: {data['real']['avg']:.2f}")
                print(f"    Sim avg: {data['simulated']['avg']:.2f}")
                print(f"    Difference: {data['percent_difference']:.1f}%")