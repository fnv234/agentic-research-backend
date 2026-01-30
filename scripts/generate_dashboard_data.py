"""
Generate and save simulation data for dashboard display.
Creates realistic simulation runs with F1-F4 inputs and all outputs.
"""

import json
import random
from datetime import datetime, timedelta
from data.forio_data_api import ForioDataAPI

def generate_realistic_runs(n=10):
    """Generate realistic simulation runs with F1-F4 and all outputs."""
    runs = []
    
    strategies = [
        {'name': 'Balanced', 'F1': 30, 'F2': 30, 'F3': 25, 'F4': 15},
        {'name': 'Prevention-Heavy', 'F1': 50, 'F2': 25, 'F3': 15, 'F4': 10},
        {'name': 'Detection-Heavy', 'F1': 20, 'F2': 50, 'F3': 20, 'F4': 10},
        {'name': 'Response-Heavy', 'F1': 15, 'F2': 20, 'F3': 45, 'F4': 20},
        {'name': 'Recovery-Heavy', 'F1': 20, 'F2': 20, 'F3': 20, 'F4': 40},
        {'name': 'Proactive', 'F1': 45, 'F2': 45, 'F3': 5, 'F4': 5},
        {'name': 'Reactive', 'F1': 10, 'F2': 15, 'F3': 40, 'F4': 35},
        {'name': 'Moderate', 'F1': 35, 'F2': 30, 'F3': 20, 'F4': 15},
        {'name': 'Conservative', 'F1': 40, 'F2': 35, 'F3': 15, 'F4': 10},
        {'name': 'Aggressive', 'F1': 25, 'F2': 25, 'F3': 30, 'F4': 20},
    ]
    
    base_time = datetime.now() - timedelta(days=30)
    
    for i, strategy in enumerate(strategies[:n]):
        f1, f2, f3, f4 = strategy['F1'], strategy['F2'], strategy['F3'], strategy['F4']
        
        # Calculate realistic outputs based on inputs
        # Prevention (F1) reduces compromised systems and increases profits
        # Detection (F2) helps catch issues early
        # Response (F3) reduces impact when incidents occur
        # Recovery (F4) helps restore systems quickly
        
        base_profit = 1000000
        profit = base_profit + (f1 * 12000) + (f2 * 8000) - (f3 * 5000) - (f4 * 3000) + random.randint(-150000, 150000)
        accumulated_profit = profit * random.uniform(0.9, 1.1)
        
        # Compromised systems: lower with more prevention and detection
        compromised = max(0, 25 - (f1 // 3) - (f2 // 5) - (f3 // 7) - (f4 // 10) + random.randint(-3, 3))
        
        # Systems availability: higher with more investment
        availability = min(1.0, 0.80 + (f1 * 0.002) + (f2 * 0.0015) + (f3 * 0.001) + (f4 * 0.0005) + random.uniform(-0.05, 0.05))
        
        # Additional outputs
        systems_at_risk = max(0, 15 - (f1 // 4) + random.randint(-2, 2))
        fraction_to_make_profits = min(1.0, max(0.0, 0.7 - (f1 + f2 + f3 + f4) / 200 + random.uniform(-0.1, 0.1)))
        impact_on_business = max(0, 10 - (f1 // 5) - (f2 // 6) - (f3 // 4) - (f4 // 3) + random.randint(-2, 2))
        
        # Data API requires IDs to match [a-zA-Z0-9-]+ (no underscores)
        safe_name = strategy['name'].lower().replace(' ', '-').replace('_', '-')
        run = {
            'id': f"run-{i+1}-{safe_name}",
            'strategy': strategy['name'],
            'F1': f1,
            'F2': f2,
            'F3': f3,
            'F4': f4,
            'prevention_budget': f1,
            'detection_budget': f2,
            'response_budget': f3,
            'recovery_budget': f4,
            'accumulated_profit': round(accumulated_profit, 2),
            'profits': round(profit, 2),
            'compromised_systems': int(compromised),
            'systems_availability': round(availability, 3),
            'systems_at_risk': int(systems_at_risk),
            'fraction_to_make_profits': round(fraction_to_make_profits, 3),
            'impact_on_business': round(impact_on_business, 2),
            'created': (base_time + timedelta(days=i*3)).isoformat(),
            'user': 'MIT@2025002',
            'group': 'default',
            'source': 'generated'
        }
        
        runs.append(run)
    
    return runs


def save_data_for_dashboard(runs, save_to_data_api=True):
    """Save runs in format dashboard can use."""
    
    # Save to simulation_data.json (dashboard looks for this)
    data_dict = {run['id']: run for run in runs}
    with open('simulation_data.json', 'w') as f:
        json.dump(data_dict, f, indent=2, default=str)
    print(f"Saved {len(runs)} runs to simulation_data.json")
    
    # Also save as list format (automated_dataset.json)
    with open('automated_dataset.json', 'w') as f:
        json.dump(runs, f, indent=2, default=str)
    print(f"Saved {len(runs)} runs to automated_dataset.json")
    
    # Save to Data API if configured
    if save_to_data_api:
        try:
            api = ForioDataAPI()
            if api.is_configured():
                print(f"\nSaving to Forio Data API...")
                saved_count = 0
                for run in runs:
                    # Use POST to auto-generate ID (avoids ID format issues)
                    # Or use PUT with properly formatted ID
                    doc_id = run['id'].replace('_', '-')  # Ensure no underscores
                    saved = api.save_simulation_result(run, document_id=doc_id)
                    if saved:
                        saved_count += 1
                    else:
                        # Try with POST (auto-generated ID) if PUT fails
                        saved = api.save_simulation_result(run, document_id=None)
                        if saved:
                            saved_count += 1
                print(f"Saved {saved_count}/{len(runs)} runs to Data API")
            else:
                print("Data API not configured, skipping Data API save")
        except Exception as e:
            print(f"Could not save to Data API: {e}")


def main():
    print("=" * 70)
    print("Generating Dashboard Data")
    print("=" * 70)
    
    print("\nGenerating simulation runs...")
    runs = generate_realistic_runs(n=10)
    
    print(f"\nGenerated {len(runs)} simulation runs")
    print("\nSample run:")
    sample = runs[0]
    print(f"  Strategy: {sample['strategy']}")
    print(f"  F1-F4: {sample['F1']}%, {sample['F2']}%, {sample['F3']}%, {sample['F4']}%")
    print(f"  Accumulated Profit: ${sample['accumulated_profit']:,.0f}")
    print(f"  Compromised Systems: {sample['compromised_systems']}")
    print(f"  Systems Availability: {sample['systems_availability']:.1%}")
    
    print("\nSaving data...")
    save_data_for_dashboard(runs, save_to_data_api=True)
    
    print("\n" + "=" * 70)
    print("Data generation complete!")
    print("=" * 70)


if __name__ == '__main__':
    main()

