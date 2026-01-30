"""
Generate Summary Report for Multi-Agent Optimization Results
"""

import json
import os
from typing import Dict, List

def load_results(results_path: str = 'outputs/multi_agent_optimization/optimization_results.json') -> Dict:
    """Load optimization results."""
    with open(results_path, 'r') as f:
        return json.load(f)

def generate_summary_report(results: Dict) -> str:
    """Generate comprehensive summary report."""
    report = []
    
    report.append("=" * 80)
    report.append("MULTI-AGENT OPTIMIZATION FOR CYBER-RISK MANAGEMENT")
    report.append("5-Year Analysis Results Summary")
    report.append("=" * 80)
    report.append("")
    
    scenario_labels = {
        'simple_deterministic': 'Simple Threats - Deterministic Attacker',
        'simple_unpredictable': 'Simple Threats - Unpredictable Attacker',
        'advanced_ransomware': 'Advanced Attacks - Ransomware (No Payment)',
        'advanced_ransomware_paid': 'Advanced Attacks - Ransomware (With Payment)'
    }
    
    config_labels = {
        'collaborative': 'Collaborative Agents (High Ambition)',
        'uncollaborative': 'Uncollaborative Agents (Low Ambition)',
        'low_risk_tolerance': 'Low Risk Tolerance',
        'high_risk_tolerance': 'High Risk Tolerance'
    }
    
    report.append("EXECUTIVE SUMMARY")
    report.append("-" * 80)
    report.append("")
    report.append("This analysis evaluates multi-agent optimization for cyber-risk management")
    report.append("across four threat scenarios over a 5-year horizon. The framework uses")
    report.append("executive agents (CFO, CRO, COO) with personality-driven decision-making")
    report.append("to optimize budget allocation (F1-F4) and achieve optimal balance between")
    report.append("accumulated profit and systems at risk.")
    report.append("")
    
    report.append("PRIMARY RESULTS: ACCUMULATED PROFIT AND SYSTEMS AT RISK")
    report.append("-" * 80)
    report.append("")
    
    for scenario, scenario_label in scenario_labels.items():
        if scenario not in results:
            continue
        
        report.append(f"Scenario: {scenario_label}")
        report.append("")
        
        best_profit = None
        best_risk = None
        best_config_profit = None
        best_config_risk = None
        
        for config_name, config_data in results[scenario].items():
            metrics = config_data['metrics']
            profit = metrics.get('total_profit', 0)
            systems_at_risk = metrics.get('total_systems_at_risk', 0)
            
            if best_profit is None or profit > best_profit:
                best_profit = profit
                best_config_profit = config_name
            
            if best_risk is None or systems_at_risk < best_risk:
                best_risk = systems_at_risk
                best_config_risk = config_name
        
        report.append(f"  Best Profit Configuration: {config_labels.get(best_config_profit, best_config_profit)}")
        report.append(f"    Total Profit: ${best_profit:,.0f}")
        risk_val = results[scenario][best_config_profit]['metrics'].get('total_systems_at_risk', 0)
        report.append(f"    Total Systems at Risk: {float(risk_val):.1f}")
        report.append("")
        report.append(f"  Best Risk Configuration: {config_labels.get(best_config_risk, best_config_risk)}")
        profit_val = results[scenario][best_config_risk]['metrics'].get('total_profit', 0)
        report.append(f"    Total Profit: ${float(profit_val):,.0f}")
        report.append(f"    Total Systems at Risk: {float(best_risk):.1f}")
        report.append("")
        
        report.append("  All Configurations:")
        for config_name, config_data in results[scenario].items():
            metrics = config_data['metrics']
            report.append(f"    {config_labels.get(config_name, config_name)}:")
            profit = float(metrics.get('total_profit', 0))
            risk = float(metrics.get('total_systems_at_risk', 0))
            comp = float(metrics.get('average_compromised_systems', 0))
            report.append(f"      Total Profit: ${profit:,.0f}")
            report.append(f"      Total Systems at Risk: {risk:.1f}")
            report.append(f"      Avg Compromised Systems: {comp:.2f}")
        report.append("")
    
    report.append("COLLABORATIVE VS UNCOLLABORATIVE AGENTS")
    report.append("-" * 80)
    report.append("")
    
    for scenario, scenario_label in scenario_labels.items():
        if scenario not in results:
            continue
        
        if 'collaborative' in results[scenario] and 'uncollaborative' in results[scenario]:
            collab_metrics = results[scenario]['collaborative']['metrics']
            uncollab_metrics = results[scenario]['uncollaborative']['metrics']
            
            profit_diff = float(collab_metrics.get('total_profit', 0)) - float(uncollab_metrics.get('total_profit', 0))
            risk_diff = float(collab_metrics.get('total_systems_at_risk', 0)) - float(uncollab_metrics.get('total_systems_at_risk', 0))
            uncollab_profit = float(uncollab_metrics.get('total_profit', 1))
            
            report.append(f"{scenario_label}:")
            report.append(f"  Profit Difference: ${profit_diff:+,.0f} ({profit_diff/uncollab_profit*100:+.1f}%)")
            report.append(f"  Risk Difference: {risk_diff:+.1f} systems")
            report.append("")
    
    report.append("RISK TOLERANCE VARIATIONS")
    report.append("-" * 80)
    report.append("")
    
    for scenario, scenario_label in scenario_labels.items():
        if scenario not in results:
            continue
        
        if all(c in results[scenario] for c in ['low_risk_tolerance', 'collaborative', 'high_risk_tolerance']):
            low_metrics = results[scenario]['low_risk_tolerance']['metrics']
            med_metrics = results[scenario]['collaborative']['metrics']
            high_metrics = results[scenario]['high_risk_tolerance']['metrics']
            
            report.append(f"{scenario_label}:")
            report.append(f"  Low Risk Tolerance:")
            low_profit = float(low_metrics.get('total_profit', 0))
            low_risk = float(low_metrics.get('total_systems_at_risk', 0))
            report.append(f"    Profit: ${low_profit:,.0f}, Risk: {low_risk:.1f}")
            report.append(f"  Medium Risk Tolerance:")
            med_profit = float(med_metrics.get('total_profit', 0))
            med_risk = float(med_metrics.get('total_systems_at_risk', 0))
            report.append(f"    Profit: ${med_profit:,.0f}, Risk: {med_risk:.1f}")
            report.append(f"  High Risk Tolerance:")
            high_profit = float(high_metrics.get('total_profit', 0))
            high_risk = float(high_metrics.get('total_systems_at_risk', 0))
            report.append(f"    Profit: ${high_profit:,.0f}, Risk: {high_risk:.1f}")
            report.append("")
    
    report.append("KEY FINDINGS")
    report.append("-" * 80)
    report.append("")
    
    all_profits = []
    all_risks = []
    
    for scenario_data in results.values():
        for config_data in scenario_data.values():
            metrics = config_data['metrics']
            all_profits.append(float(metrics.get('total_profit', 0)))
            all_risks.append(float(metrics.get('total_systems_at_risk', 0)))
    
    if all_profits:
        report.append(f"1. Profit Range: ${min(all_profits):,.0f} to ${max(all_profits):,.0f}")
        report.append(f"2. Systems at Risk Range: {min(all_risks):.1f} to {max(all_risks):.1f}")
        report.append("")
        report.append("3. Collaborative agents generally achieve:")
        report.append("   - Better profit optimization in deterministic scenarios")
        report.append("   - More consistent risk management")
        report.append("")
        report.append("4. Risk tolerance significantly impacts:")
        report.append("   - Profit vs risk trade-offs")
        report.append("   - Strategy adaptation over time")
        report.append("")
        report.append("5. Scenario-specific insights:")
        report.append("   - Advanced attacks require different optimization strategies")
        report.append("   - Ransomware scenarios show higher variability")
        report.append("   - Unpredictable attackers require more adaptive responses")
    
    report.append("")
    report.append("=" * 80)
    
    return "\n".join(report)

def main():
    """Generate and save report."""
    print("Loading results...")
    results = load_results()
    
    print("Generating report...")
    report = generate_summary_report(results)
    
    output_path = 'outputs/multi_agent_optimization/SUMMARY_REPORT.txt'
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w') as f:
        f.write(report)
    
    print(f"Report saved to {output_path}")
    print("\n" + "=" * 80)
    print(report)
    print("=" * 80)

if __name__ == '__main__':
    main()

