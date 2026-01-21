"""Quick test to see if enhanced extraction works without group filtering."""

from forio_data_extractor import ForioDataExtractor

extractor = ForioDataExtractor()

print("Testing without group filter...")
runs = extractor.fetch_runs_with_variables(
    variables=['accumulated_profit', 'compromised_systems', 'systems_availability'],
    groups=None,  # No group filter
    start_record=0,
    end_record=5
)

print(f"Fetched {len(runs)} runs")

if runs:
    sample = runs[0]
    print(f"\nSample run:")
    print(f"  ID: {sample.get('id')}")
    print(f"  Created: {sample.get('created')}")
    print(f"  User: {sample.get('user', {}).get('userName')}")
    print(f"  Has variables: {bool(sample.get('variables'))}")
    if sample.get('variables'):
        print(f"  Variable keys: {list(sample['variables'].keys())}")
