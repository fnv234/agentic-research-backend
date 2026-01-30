"""
Agent Calibration Tool
Analyzes actual simulation data to recommend optimal agent targets and personalities.
"""

import json
import statistics
from forio_data_extractor import ForioDataExtractor
from multi_agent_demo_mock import generate_mock_runs

def analyze_data_distribution(runs, variables):
    """Analyze the distribution of KPI values across runs."""
    analysis = {}
    
    for var in variables:
        values = []
        for run in runs:
            val = run.get(var)
            if val is None and 'variables' in run:
                val = run['variables'].get(var)
            if val is not None:
                values.append(val)
        
        if values:
            analysis[var] = {
                'min': min(values),
                'max': max(values),
                'mean': statistics.mean(values),
                'median': statistics.median(values),
                'stdev': statistics.stdev(values) if len(values) > 1 else 0,
                'count': len(values)
            }
    
    return analysis


def recommend_targets(analysis, percentile=0.7):
    """
    Recommend agent targets based on data distribution.
    
    Args:
        analysis: Data distribution analysis
        percentile: Target percentile (0.7 = aim for top 30%)
    """
    recommendations = {}
    
    if 'accumulated_profit' in analysis:
        stats = analysis['accumulated_profit']
        target = stats['mean'] + (0.5 * stats['stdev'])
        recommendations['CFO'] = {
            'target': {'min': round(target, -3)},  # Round to nearest 1000
            'rationale': f"Based on mean ${stats['mean']:,.0f} + 0.5 stdev"
        }
    
    if 'compromised_systems' in analysis:
        stats = analysis['compromised_systems']
        target = stats['mean'] - (0.5 * stats['stdev'])
        recommendations['CRO'] = {
            'target': {'max': max(0, round(target))},
            'rationale': f"Based on mean {stats['mean']:.1f} - 0.5 stdev"
        }
    
    if 'systems_availability' in analysis:
        stats = analysis['systems_availability']
        target = stats['mean'] + (0.3 * stats['stdev'])
        recommendations['COO'] = {
            'target': {'min': round(target, 2)},
            'rationale': f"Based on mean {stats['mean']:.2%} + 0.3 stdev"
        }
    
    return recommendations


def recommend_personalities(analysis):
    """
    Recommend personality traits based on data characteristics.
    """
    recommendations = {}
    
    if 'accumulated_profit' in analysis:
        stats = analysis['accumulated_profit']
        cv = stats['stdev'] / stats['mean'] if stats['mean'] > 0 else 0  # Coefficient of variation
        
        risk_tolerance = min(0.8, 0.3 + (cv * 2))
        
        recommendations['CFO'] = {
            'risk_tolerance': round(risk_tolerance, 2),
            'friendliness': 0.6,  # Moderate
            'ambition': 0.8,  # High (CFO wants growth)
            'rationale': f"Profit CV={cv:.2f}, suggests risk_tolerance={risk_tolerance:.2f}"
        }
    
    if 'compromised_systems' in analysis:
        stats = analysis['compromised_systems']
        
        cv = stats['stdev'] / stats['mean'] if stats['mean'] > 0 else 0
        risk_tolerance = min(0.4, 0.15 + (cv * 0.5))
        
        recommendations['CRO'] = {
            'risk_tolerance': round(risk_tolerance, 2),
            'friendliness': 0.5,  # Moderate
            'ambition': 0.6,  # Moderate-high
            'rationale': f"Security CV={cv:.2f}, CRO should be cautious"
        }
    
    if 'systems_availability' in analysis:
        stats = analysis['systems_availability']
        
        recommendations['COO'] = {
            'risk_tolerance': 0.5,  # Balanced
            'friendliness': 0.7,  # Collaborative
            'ambition': 0.7,  # High
            'rationale': "Operations requires balanced approach"
        }
    
    return recommendations


def test_calibration(runs, targets, personalities):
    """
    Test how agents would perform with new calibration.
    Returns distribution of agent responses.
    """
    from multi_agent_demo_mock import ExecutiveBot, BoardRoom
    
    cfo = ExecutiveBot("CFO", "accumulated_profit", 
                       target=targets.get('CFO', {}).get('target', {}),
                       personality=personalities.get('CFO', {}))
    
    cro = ExecutiveBot("CRO", "compromised_systems",
                       target=targets.get('CRO', {}).get('target', {}),
                       personality=personalities.get('CRO', {}))
    
    coo = ExecutiveBot("COO", "systems_availability",
                       target=targets.get('COO', {}).get('target', {}),
                       personality=personalities.get('COO', {}))
    
    board = BoardRoom([cfo, cro, coo])
    
    results = {
        'below_target': 0,
        'on_target': 0,
        'above_target': 0
    }
    
    for run in runs:
        feedback = board.run_meeting(run)
        for comment in feedback:
            if 'below target' in comment:
                results['below_target'] += 1
            elif 'above target' in comment:
                results['above_target'] += 1
            else:
                results['on_target'] += 1
    
    total = sum(results.values())
    return {
        'below_target_pct': results['below_target'] / total if total > 0 else 0,
        'on_target_pct': results['on_target'] / total if total > 0 else 0,
        'above_target_pct': results['above_target'] / total if total > 0 else 0,
        'total_evaluations': total
    }


if __name__ == '__main__':
    print("=" * 70)
    print("Agent Calibration Tool")
    print("=" * 70)
    
    print("\nFetching simulation data...")
    try:
        extractor = ForioDataExtractor()
        runs = extractor.fetch_runs_with_variables(
            variables=['accumulated_profit', 'compromised_systems', 'systems_availability',
                      'prevention_budget', 'detection_budget', 'response_budget'],
            start_record=0,
            end_record=50
        )
        
        has_data = any(run.get('variables') for run in runs)
        
        if not has_data or len(runs) < 5:
            print("Insufficient data, using mock data.")
            runs = generate_mock_runs(20)
        else:
            print(f"Using {len(runs)} real simulation runs")
    except:
        print("Could not fetch data, using mock data.")
        runs = generate_mock_runs(20)
    
    print("\nAnalyzing data distribution...")
    variables = ['accumulated_profit', 'compromised_systems', 'systems_availability']
    analysis = analyze_data_distribution(runs, variables)
    
    print("\nData Statistics:")
    for var, stats in analysis.items():
        print(f"\n   {var}:")
        print(f"      Range: {stats['min']:,.2f} - {stats['max']:,.2f}")
        print(f"      Mean: {stats['mean']:,.2f}")
        print(f"      Median: {stats['median']:,.2f}")
        print(f"      Std Dev: {stats['stdev']:,.2f}")
    
    print("\nRecommending agent targets...")
    target_recommendations = recommend_targets(analysis)
    
    print("\nRecommended Targets:")
    for agent, rec in target_recommendations.items():
        print(f"\n   {agent}:")
        print(f"      Target: {rec['target']}")
        print(f"      Rationale: {rec['rationale']}")
    
    print("\nRecommending personality traits...")
    personality_recommendations = recommend_personalities(analysis)
    
    print("\nRecommended Personalities:")
    for agent, rec in personality_recommendations.items():
        print(f"\n   {agent}:")
        print(f"      Risk Tolerance: {rec['risk_tolerance']}")
        print(f"      Friendliness: {rec['friendliness']}")
        print(f"      Ambition: {rec['ambition']}")
        print(f"      Rationale: {rec['rationale']}")
    
    print("\nTesting calibration...")
    test_results = test_calibration(runs, target_recommendations, personality_recommendations)
    
    print("\nCalibration Test Results:")
    print(f"      Below Target: {test_results['below_target_pct']:.1%}")
    print(f"      On Target: {test_results['on_target_pct']:.1%}")
    print(f"      Above Target: {test_results['above_target_pct']:.1%}")
    print(f"\nIdeal distribution: ~30% below, ~40% on, ~30% above")
    
    print("\nGenerating configuration...")
    config = {
        'agents': {
            'CFO': {
                'kpi_focus': 'accumulated_profit',
                'target': target_recommendations.get('CFO', {}).get('target', {}),
                'personality': personality_recommendations.get('CFO', {})
            },
            'CRO': {
                'kpi_focus': 'compromised_systems',
                'target': target_recommendations.get('CRO', {}).get('target', {}),
                'personality': personality_recommendations.get('CRO', {})
            },
            'COO': {
                'kpi_focus': 'systems_availability',
                'target': target_recommendations.get('COO', {}).get('target', {}),
                'personality': personality_recommendations.get('COO', {})
            }
        },
        'calibration_metadata': {
            'based_on_runs': len(runs),
            'data_source': 'real' if any(run.get('variables') for run in runs) else 'mock',
            'variables_analyzed': variables
        }
    }
    
    with open('agent_calibration.json', 'w') as f:
        json.dump(config, f, indent=2)
    
    print("Saved to agent_calibration.json")
    
    print("\n" + "=" * 70)
    print("CALIBRATION COMPLETE")
    print("=" * 70)
    
    print("\nNext steps:")
    print("Review agent_calibration.json")
    print("Update dashboard.py with new targets/personalities")
    print("Test with: python dashboard.py")
    print()
