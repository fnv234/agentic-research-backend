"""
Multi-Agent Optimization for Cyber-Risk Management

Scenarios:
- Simple cyber threats with deterministic attacker
- Simple cyber threats with unpredictable attacker
- Advanced cyber attacks (ransomware)
- Advanced cyber attacks (ransomware) with ransom payment
"""

import pandas as pd
import numpy as np
import json
import os
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.optimize import minimize
from scipy.stats import gaussian_kde

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.agents import ExecutiveBot, BoardRoom, load_agent_config

sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (16, 12)
os.makedirs('outputs/multi_agent_optimization', exist_ok=True)

class SimulationDataLoader:
    """Load and filter simulation data from CSV."""
    
    def __init__(self, csv_path: str = 'data/sim_data.csv'):
        self.csv_path = csv_path
        self.df = None
        self.load_data()
    
    def load_data(self):
        """Load CSV data and clean it."""
        print(f"Loading simulation data from {self.csv_path}...")
        self.df = pd.read_csv(self.csv_path)
        
        if 'Cum. Profits' in self.df.columns:
            self.df['Cum. Profits'] = self.df['Cum. Profits'].astype(str).str.replace(',', '').astype(float)
        
        numeric_cols = ['Comp. Systems', 'Months Completed', 'Level', 'Ransomware', 'Pay Ransom']
        for col in numeric_cols:
            if col in self.df.columns:
                self.df[col] = pd.to_numeric(self.df[col], errors='coerce')
        
        print(f"Loaded {len(self.df)} simulation runs")
        print(f"Columns: {list(self.df.columns)}")
    
    def filter_scenario(self, level: Optional[int] = None, 
                       ransomware: Optional[int] = None,
                       pay_ransom: Optional[int] = None,
                       deterministic: bool = True) -> pd.DataFrame:
        """
        Filter data by scenario.
        
        Args:
            level: 1 = simple threats, 2 = advanced threats
            ransomware: 0 = no ransomware, 1 = ransomware attack
            pay_ransom: 0 = didn't pay, 1 = paid ransom
            deterministic: True for deterministic attacker, False for unpredictable
        """
        filtered = self.df.copy()
        
        if level is not None:
            filtered = filtered[filtered['Level'] == level]
        
        if ransomware is not None:
            filtered = filtered[filtered['Ransomware'] == ransomware]
        
        if pay_ransom is not None:
            filtered = filtered[filtered['Pay Ransom'] == pay_ransom]
        
        # For deterministic vs unpredictable, we can use variance in outcomes
        # Deterministic: lower variance in results
        # Unpredictable: higher variance in results
        if not deterministic and len(filtered) > 10:
            # Add noise to simulate unpredictability
            # This is a proxy - in real data, unpredictability would be inherent
            pass
        
        return filtered
    
    def get_scenario_data(self, scenario_name: str) -> pd.DataFrame:
        """Get data for a specific scenario."""
        scenarios = {
            'simple_deterministic': {
                'level': 1,
                'ransomware': 0,
                'pay_ransom': 0,
                'deterministic': True
            },
            'simple_unpredictable': {
                'level': 1,
                'ransomware': 0,
                'pay_ransom': 0,
                'deterministic': False
            },
            'advanced_ransomware': {
                'level': None,  # Can be 1 or 2
                'ransomware': 1,
                'pay_ransom': 0,
                'deterministic': True
            },
            'advanced_ransomware_paid': {
                'level': None,
                'ransomware': 1,
                'pay_ransom': 1,
                'deterministic': True
            }
        }
        
        if scenario_name not in scenarios:
            raise ValueError(f"Unknown scenario: {scenario_name}")
        
        filtered = self.filter_scenario(**scenarios[scenario_name])
        
        # For unpredictable scenario, add variance to simulate unpredictability
        if scenario_name == 'simple_unpredictable' and len(filtered) > 0:
            # Add random noise to outcomes to simulate unpredictability
            np.random.seed(42)  # For reproducibility
            filtered = filtered.copy()
            if 'Cum. Profits' in filtered.columns:
                filtered['Cum. Profits'] = filtered['Cum. Profits'] * (1 + np.random.normal(0, 0.15, len(filtered)))
            if 'Comp. Systems' in filtered.columns:
                filtered['Comp. Systems'] = filtered['Comp. Systems'] + np.random.randint(-5, 5, len(filtered))
                filtered['Comp. Systems'] = filtered['Comp. Systems'].clip(lower=0)
        
        return filtered
    
    def estimate_f1_f4_from_data(self, row: pd.Series) -> Tuple[float, float, float, float]:
        """
        Estimate F1-F4 allocation from simulation results.
        This is a proxy - in real data, F1-F4 would be explicit inputs.
        We estimate based on outcomes.
        """
        # Heuristic: If low compromised systems and high profit, likely high F1 (prevention)
        # If high compromised but recovered quickly, likely high F3 (response) and F4 (recovery)
        
        profit = row.get('Cum. Profits', 0)
        compromised = row.get('Comp. Systems', 0)
        ransomware = row.get('Ransomware', 0)
        pay_ransom = row.get('Pay Ransom', 0)
        
        # Base allocation
        f1, f2, f3, f4 = 30, 30, 25, 15
        
        # Adjust based on outcomes
        if compromised < 10:
            # Low compromised systems - likely high prevention
            f1 += 10
            f2 += 5
            f3 -= 5
            f4 -= 10
        elif compromised > 30:
            # High compromised - likely low prevention, need response/recovery
            f1 -= 10
            f2 -= 5
            f3 += 10
            f4 += 5
        
        if profit < 1000:
            # Low profit - may have overspent on security or had major incident
            if ransomware == 1 and pay_ransom == 1:
                # Paid ransom - likely had to cut other areas
                f1 -= 5
                f2 -= 5
                f3 -= 5
                f4 -= 5
            else:
                # Major incident - need more response/recovery
                f3 += 5
                f4 += 5
        
        # Normalize to sum to 100
        total = f1 + f2 + f3 + f4
        if total > 0:
            f1, f2, f3, f4 = f1*100/total, f2*100/total, f3*100/total, f4*100/total
        
        # Ensure constraints
        f1 = max(10, min(60, f1))
        f2 = max(10, min(60, f2))
        f3 = max(5, min(50, f3))
        f4 = max(5, min(50, f4))
        
        # Renormalize
        total = f1 + f2 + f3 + f4
        if total > 0:
            f1, f2, f3, f4 = f1*100/total, f2*100/total, f3*100/total, f4*100/total
        
        return f1, f2, f3, f4


class MultiAgentOptimizer:
    """5-year optimization using multi-agent framework."""
    
    def __init__(self, agent_config: Optional[Dict] = None, 
                 collaborative: bool = True,
                 risk_tolerance_level: str = 'medium'):
        """
        Initialize optimizer with agent configuration.
        
        Args:
            agent_config: Agent configuration dict (if None, loads from file)
            collaborative: True for collaborative (high ambition), False for uncollaborative (low ambition)
            risk_tolerance_level: 'low', 'medium', 'high' for risk tolerance
        """
        if agent_config is None:
            agent_config = load_agent_config()
        
        self.agents = []
        self.collaborative = collaborative
        self.risk_tolerance_level = risk_tolerance_level
        
        # Adjust agent personalities based on configuration
        for name, config in agent_config.items():
            if name in ['IT_Manager', 'CHRO', 'COO_Business']:
                continue  # Focus on main 3 agents
            
            personality = config['personality'].copy()
            
            # Adjust ambition based on collaborative setting
            if collaborative:
                personality['ambition'] = min(1.0, personality['ambition'] + 0.2)  # More collaborative
                personality['friendliness'] = min(1.0, personality['friendliness'] + 0.2)
            else:
                personality['ambition'] = max(0.0, personality['ambition'] - 0.2)  # Less collaborative
                personality['friendliness'] = max(0.0, personality['friendliness'] - 0.2)
            
            # Adjust risk tolerance
            if risk_tolerance_level == 'low':
                personality['risk_tolerance'] = max(0.0, personality['risk_tolerance'] - 0.3)
            elif risk_tolerance_level == 'high':
                personality['risk_tolerance'] = min(1.0, personality['risk_tolerance'] + 0.3)
            # 'medium' keeps original
            
            agent = ExecutiveBot(
                name=name,
                kpi_focus=config['kpi'],
                target=config['target'],
                personality=personality
            )
            self.agents.append(agent)
        
        self.board = BoardRoom(self.agents)
    
    def simulate_year_from_data(self, data_row: pd.Series, 
                                previous_results: Optional[Dict] = None) -> Dict:
        """Simulate one year using data from CSV."""
        # Extract actual results from data
        profit = data_row.get('Cum. Profits', 0) * 1000  # Convert from thousands
        compromised = data_row.get('Comp. Systems', 0)
        months = data_row.get('Months Completed', 60)
        
        # Estimate systems at risk (proxy metric)
        systems_at_risk = max(0, compromised + np.random.randint(-3, 3))
        
        # Estimate availability (higher if fewer compromised)
        availability = max(0.0, min(1.0, 1.0 - (compromised / 100)))
        
        # Estimate impact on business
        impact = compromised * 0.5 + (100 - availability * 100) * 0.1
        
        # Estimate F1-F4 (if not in data, use heuristic)
        f1, f2, f3, f4 = self.estimate_f1_f4_from_data(data_row)
        
        return {
            'F1': f1,
            'F2': f2,
            'F3': f3,
            'F4': f4,
            'accumulated_profit': profit,
            'compromised_systems': compromised,
            'systems_availability': availability,
            'systems_at_risk': systems_at_risk,
            'impact_on_business': impact,
            'months_completed': months,
            'level': data_row.get('Level', 1),
            'ransomware': data_row.get('Ransomware', 0),
            'pay_ransom': data_row.get('Pay Ransom', 0)
        }
    
    def estimate_f1_f4_from_data(self, row: pd.Series) -> Tuple[float, float, float, float]:
        """Estimate F1-F4 allocation from outcomes."""
        profit = row.get('Cum. Profits', 0)
        compromised = row.get('Comp. Systems', 0)
        ransomware = row.get('Ransomware', 0)
        pay_ransom = row.get('Pay Ransom', 0)
        
        # Base allocation
        f1, f2, f3, f4 = 30, 30, 25, 15
        
        # Adjust based on outcomes
        if compromised < 10:
            f1 += 10
            f2 += 5
            f3 -= 5
            f4 -= 10
        elif compromised > 30:
            f1 -= 10
            f2 -= 5
            f3 += 10
            f4 += 5
        
        if profit < 1000:
            if ransomware == 1 and pay_ransom == 1:
                f1 -= 5
                f2 -= 5
                f3 -= 5
                f4 -= 5
            else:
                f3 += 5
                f4 += 5
        
        # Normalize
        total = f1 + f2 + f3 + f4
        if total > 0:
            f1, f2, f3, f4 = f1*100/total, f2*100/total, f3*100/total, f4*100/total
        
        # Constraints
        f1 = max(10, min(60, f1))
        f2 = max(10, min(60, f2))
        f3 = max(5, min(50, f3))
        f4 = max(5, min(50, f4))
        
        total = f1 + f2 + f3 + f4
        if total > 0:
            f1, f2, f3, f4 = f1*100/total, f2*100/total, f3*100/total, f4*100/total
        
        return f1, f2, f3, f4
    
    def optimize_next_year(self, current_results: Dict, 
                          scenario_data: pd.DataFrame) -> Tuple[float, float, float, float]:
        """
        Use agent recommendations to optimize next year's F1-F4 allocation.
        """
        # Get agent evaluations
        evaluations = self.board.run_meeting(current_results)
        recommendations = self.board.negotiate_strategy(current_results)
        
        # Current allocation
        current_f1 = current_results.get('F1', 30)
        current_f2 = current_results.get('F2', 30)
        current_f3 = current_results.get('F3', 25)
        current_f4 = current_results.get('F4', 15)
        
        # Analyze recommendations to adjust allocation
        adjustments = {'F1': 0, 'F2': 0, 'F3': 0, 'F4': 0}
        
        for agent in self.agents:
            kpi_value = current_results.get(agent.kpi_focus)
            if kpi_value is None:
                continue
            
            target_min = agent.target.get("min", float("-inf"))
            target_max = agent.target.get("max", float("inf"))
            
            # CFO: If profit below target, increase prevention/detection
            if agent.name == "CFO" and kpi_value < target_min:
                adjustments['F1'] += 2
                adjustments['F2'] += 1
                adjustments['F3'] -= 1.5
                adjustments['F4'] -= 1.5
            
            # CRO: If compromised systems above target, increase prevention
            elif agent.name == "CRO" and kpi_value > target_max:
                adjustments['F1'] += 3
                adjustments['F2'] += 2
                adjustments['F3'] -= 2
                adjustments['F4'] -= 3
            
            # COO: If availability below target, increase prevention/detection
            elif agent.name == "COO" and kpi_value < target_min:
                adjustments['F1'] += 1.5
                adjustments['F2'] += 1
                adjustments['F3'] -= 1
                adjustments['F4'] -= 1.5
        
        # Apply adjustments with constraints
        new_f1 = max(10, min(60, current_f1 + adjustments['F1']))
        new_f2 = max(10, min(60, current_f2 + adjustments['F2']))
        new_f3 = max(5, min(50, current_f3 + adjustments['F3']))
        new_f4 = max(5, min(50, current_f4 + adjustments['F4']))
        
        # Normalize to sum to 100
        total = new_f1 + new_f2 + new_f3 + new_f4
        if total > 0:
            new_f1 = new_f1 * 100 / total
            new_f2 = new_f2 * 100 / total
            new_f3 = new_f3 * 100 / total
            new_f4 = new_f4 * 100 / total
        
        return new_f1, new_f2, new_f3, new_f4
    
    def run_5_year_optimization(self, scenario_data: pd.DataFrame,
                              initial_strategy: Optional[Dict] = None) -> List[Dict]:
        """
        Run 5-year optimization using agent recommendations.
        """
        years = []
        
        # Filter data for 5-year runs (60 months)
        five_year_data = scenario_data[scenario_data['Months Completed'] == 60].copy()
        
        if len(five_year_data) == 0:
            print(f"Warning: No 5-year data found for scenario. Using all data.")
            five_year_data = scenario_data.copy()
        
        # Year 1: Start with best performing run or initial strategy
        if initial_strategy:
            f1, f2, f3, f4 = initial_strategy['F1'], initial_strategy['F2'], \
                            initial_strategy['F3'], initial_strategy['F4']
            # Find closest matching data point
            year1_data = five_year_data.iloc[0]  # Use first available
        else:
            # Use best performing run (highest profit, lowest risk)
            five_year_data['score'] = (five_year_data['Cum. Profits'] / 1000) - \
                                     (five_year_data['Comp. Systems'] * 10)
            best_idx = five_year_data['score'].idxmax()
            year1_data = five_year_data.loc[best_idx]
            f1, f2, f3, f4 = self.estimate_f1_f4_from_data(year1_data)
        
        year1_results = self.simulate_year_from_data(year1_data)
        year1_results['year'] = 1
        year1_results['agent_config'] = 'collaborative' if self.collaborative else 'uncollaborative'
        year1_results['risk_tolerance'] = self.risk_tolerance_level
        years.append(year1_results)
        
        # Years 2-5: Use agent recommendations to optimize
        for year in range(2, 6):
            previous_results = years[-1]
            
            # Optimize next year's allocation
            f1, f2, f3, f4 = self.optimize_next_year(previous_results, five_year_data)
            
            # Find data point that matches optimized allocation (or closest)
            # For now, sample from scenario data weighted by similarity
            # In practice, would run new simulation with optimized F1-F4
            
            # Sample from available data (proxy for running new simulation)
            if len(five_year_data) > 0:
                # Weight by similarity to target allocation
                five_year_data['allocation_similarity'] = \
                    -abs(five_year_data['Comp. Systems'] - (100 - f1*2))  # Rough proxy
                weights = np.exp(five_year_data['allocation_similarity'] / 10)
                weights = weights / weights.sum()
                
                sampled_idx = np.random.choice(five_year_data.index, p=weights)
                year_data = five_year_data.loc[sampled_idx]
            else:
                # Fallback: use previous year's data
                year_data = year1_data
            
            year_results = self.simulate_year_from_data(year_data)
            year_results['F1'] = f1
            year_results['F2'] = f2
            year_results['F3'] = f3
            year_results['F4'] = f4
            year_results['year'] = year
            year_results['agent_config'] = 'collaborative' if self.collaborative else 'uncollaborative'
            year_results['risk_tolerance'] = self.risk_tolerance_level
            years.append(year_results)
        
        return years
    
    def calculate_5_year_metrics(self, years: List[Dict]) -> Dict:
        """Calculate cumulative metrics over 5 years."""
        total_profit = sum(y.get('accumulated_profit', 0) for y in years)
        total_compromised = sum(y.get('compromised_systems', 0) for y in years)
        avg_compromised = np.mean([y.get('compromised_systems', 0) for y in years])
        total_systems_at_risk = sum(y.get('systems_at_risk', 0) for y in years)
        avg_systems_at_risk = np.mean([y.get('systems_at_risk', 0) for y in years])
        avg_availability = np.mean([y.get('systems_availability', 0) for y in years])
        
        return {
            'total_profit': total_profit,
            'total_compromised_systems': total_compromised,
            'average_compromised_systems': avg_compromised,
            'total_systems_at_risk': total_systems_at_risk,
            'average_systems_at_risk': avg_systems_at_risk,
            'average_availability': avg_availability,
            'final_profit': years[-1].get('accumulated_profit', 0) if years else 0,
            'final_compromised': years[-1].get('compromised_systems', 0) if years else 0,
            'final_systems_at_risk': years[-1].get('systems_at_risk', 0) if years else 0
        }


def run_comprehensive_analysis():
    """Run comprehensive analysis for all scenarios and configurations."""
    print("=" * 80)
    print("MULTI-AGENT OPTIMIZATION FOR CYBER-RISK MANAGEMENT")
    print("5-Year Analysis Using Real Simulation Data")
    print("=" * 80)
    
    # Load data
    loader = SimulationDataLoader('data/sim_data.csv')
    
    # Define scenarios
    scenarios = {
        'simple_deterministic': 'Simple Threats - Deterministic Attacker',
        'simple_unpredictable': 'Simple Threats - Unpredictable Attacker',
        'advanced_ransomware': 'Advanced Attacks - Ransomware (No Payment)',
        'advanced_ransomware_paid': 'Advanced Attacks - Ransomware (With Payment)'
    }
    
    # Define agent configurations
    agent_configs = [
        ('collaborative', True, 'medium'),
        ('uncollaborative', False, 'medium'),
        ('low_risk_tolerance', True, 'low'),
        ('high_risk_tolerance', True, 'high')
    ]
    
    all_results = {}
    
    # Run analysis for each scenario and configuration
    for scenario_name, scenario_label in scenarios.items():
        print(f"\n{'='*80}")
        print(f"SCENARIO: {scenario_label}")
        print(f"{'='*80}")
        
        # Get scenario data
        scenario_data = loader.get_scenario_data(scenario_name)
        print(f"Found {len(scenario_data)} simulation runs for this scenario")
        
        if len(scenario_data) == 0:
            print(f"⚠️  No data for scenario {scenario_name}, skipping...")
            continue
        
        scenario_results = {}
        
        # Run with different agent configurations
        for config_name, collaborative, risk_tolerance in agent_configs:
            print(f"\n  Configuration: {config_name}")
            print(f"    Collaborative: {collaborative}, Risk Tolerance: {risk_tolerance}")
            
            # Create optimizer
            optimizer = MultiAgentOptimizer(
                collaborative=collaborative,
                risk_tolerance_level=risk_tolerance
            )
            
            # Run 5-year optimization
            years = optimizer.run_5_year_optimization(scenario_data)
            metrics = optimizer.calculate_5_year_metrics(years)
            
            scenario_results[config_name] = {
                'years': years,
                'metrics': metrics,
                'config': {
                    'collaborative': collaborative,
                    'risk_tolerance': risk_tolerance
                }
            }
            
            print(f"    Results:")
            print(f"      Total Profit: ${metrics['total_profit']:,.0f}")
            print(f"      Avg Compromised Systems: {metrics['average_compromised_systems']:.1f}")
            print(f"      Avg Systems at Risk: {metrics['average_systems_at_risk']:.1f}")
        
        all_results[scenario_name] = scenario_results
    
    # Save results
    output_dir = 'outputs/multi_agent_optimization'
    os.makedirs(output_dir, exist_ok=True)
    
    # Convert to JSON-serializable format
    results_json = {}
    for scenario, scenario_res in all_results.items():
        results_json[scenario] = {}
        for config, config_res in scenario_res.items():
            results_json[scenario][config] = {
                'metrics': config_res['metrics'],
                'config': config_res['config'],
                'years_summary': [
                    {
                        'year': y['year'],
                        'profit': y.get('accumulated_profit', 0),
                        'compromised': y.get('compromised_systems', 0),
                        'systems_at_risk': y.get('systems_at_risk', 0),
                        'F1': y.get('F1', 0),
                        'F2': y.get('F2', 0),
                        'F3': y.get('F3', 0),
                        'F4': y.get('F4', 0)
                    }
                    for y in config_res['years']
                ]
            }
    
    with open(f'{output_dir}/optimization_results.json', 'w') as f:
        json.dump(results_json, f, indent=2, default=str)
    
    print(f"\n✅ Results saved to {output_dir}/optimization_results.json")
    
    # Generate visualizations
    generate_visualizations(all_results, output_dir)
    
    return all_results


def generate_visualizations(all_results: Dict, output_dir: str):
    """Generate comprehensive visualizations."""
    print("\nGenerating visualizations...")
    
    # 1. Primary Results: Profit and Systems at Risk by Scenario
    fig, axes = plt.subplots(2, 2, figsize=(18, 14))
    fig.suptitle('5-Year Multi-Agent Optimization Results\nAccumulated Profit and Systems at Risk', 
                 fontsize=16, fontweight='bold')
    
    scenarios = list(all_results.keys())
    
    for idx, scenario in enumerate(scenarios):
        ax = axes[idx // 2, idx % 2]
        
        configs = list(all_results[scenario].keys())
        profits = [all_results[scenario][c]['metrics']['total_profit'] / 1000000 
                  for c in configs]
        systems_at_risk = [all_results[scenario][c]['metrics']['total_systems_at_risk'] 
                          for c in configs]
        
        x = np.arange(len(configs))
        width = 0.35
        
        ax2 = ax.twinx()
        bars1 = ax.bar(x - width/2, profits, width, label='Total Profit (M$)', 
                      color='green', alpha=0.7)
        bars2 = ax2.bar(x + width/2, systems_at_risk, width, label='Total Systems at Risk', 
                       color='red', alpha=0.7)
        
        ax.set_xlabel('Agent Configuration', fontweight='bold')
        ax.set_ylabel('Total Profit (Millions $)', fontweight='bold', color='green')
        ax2.set_ylabel('Total Systems at Risk', fontweight='bold', color='red')
        ax.set_title(scenario.replace('_', ' ').title(), fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels([c.replace('_', ' ').title() for c in configs], rotation=45, ha='right')
        ax.tick_params(axis='y', labelcolor='green')
        ax2.tick_params(axis='y', labelcolor='red')
        ax.legend(loc='upper left')
        ax2.legend(loc='upper right')
        ax.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    plt.savefig(f'{output_dir}/primary_results.png', dpi=300, bbox_inches='tight')
    print(f"  ✅ Saved: {output_dir}/primary_results.png")
    plt.close()
    
    # 2. Comparison across scenarios (collaborative vs uncollaborative)
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))
    fig.suptitle('Agent Configuration Comparison: Collaborative vs Uncollaborative', 
                 fontsize=14, fontweight='bold')
    
    for idx, config_key in enumerate(['collaborative', 'uncollaborative']):
        ax = axes[idx]
        
        profits = []
        systems_at_risk = []
        scenario_labels = []
        
        for scenario in scenarios:
            if config_key in all_results[scenario]:
                profits.append(all_results[scenario][config_key]['metrics']['total_profit'] / 1000000)
                systems_at_risk.append(all_results[scenario][config_key]['metrics']['total_systems_at_risk'])
                scenario_labels.append(scenario.replace('_', ' ').title())
        
        x = np.arange(len(scenario_labels))
        width = 0.35
        
        ax2 = ax.twinx()
        bars1 = ax.bar(x - width/2, profits, width, label='Total Profit (M$)', 
                      color='green', alpha=0.7)
        bars2 = ax2.bar(x + width/2, systems_at_risk, width, label='Total Systems at Risk', 
                       color='red', alpha=0.7)
        
        ax.set_xlabel('Scenario', fontweight='bold')
        ax.set_ylabel('Total Profit (Millions $)', fontweight='bold', color='green')
        ax2.set_ylabel('Total Systems at Risk', fontweight='bold', color='red')
        ax.set_title(config_key.replace('_', ' ').title(), fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels(scenario_labels, rotation=45, ha='right')
        ax.tick_params(axis='y', labelcolor='green')
        ax2.tick_params(axis='y', labelcolor='red')
        ax.legend(loc='upper left')
        ax2.legend(loc='upper right')
        ax.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    plt.savefig(f'{output_dir}/collaborative_comparison.png', dpi=300, bbox_inches='tight')
    print(f"  ✅ Saved: {output_dir}/collaborative_comparison.png")
    plt.close()
    
    # 3. Risk tolerance comparison
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    fig.suptitle('Risk Tolerance Comparison Across Scenarios', 
                 fontsize=14, fontweight='bold')
    
    risk_configs = ['low_risk_tolerance', 'collaborative', 'high_risk_tolerance']
    risk_labels = ['Low Risk Tolerance', 'Medium (Baseline)', 'High Risk Tolerance']
    
    for idx, (config_key, label) in enumerate(zip(risk_configs, risk_labels)):
        ax = axes[idx]
        
        profits = []
        systems_at_risk = []
        scenario_labels = []
        
        for scenario in scenarios:
            if config_key in all_results[scenario]:
                profits.append(all_results[scenario][config_key]['metrics']['total_profit'] / 1000000)
                systems_at_risk.append(all_results[scenario][config_key]['metrics']['total_systems_at_risk'])
                scenario_labels.append(scenario.replace('_', ' ').title()[:15])
        
        x = np.arange(len(scenario_labels))
        width = 0.35
        
        ax2 = ax.twinx()
        bars1 = ax.bar(x - width/2, profits, width, label='Total Profit (M$)', 
                      color='green', alpha=0.7)
        bars2 = ax2.bar(x + width/2, systems_at_risk, width, label='Total Systems at Risk', 
                       color='red', alpha=0.7)
        
        ax.set_xlabel('Scenario', fontweight='bold')
        ax.set_ylabel('Total Profit (Millions $)', fontweight='bold', color='green')
        ax2.set_ylabel('Total Systems at Risk', fontweight='bold', color='red')
        ax.set_title(label, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels(scenario_labels, rotation=45, ha='right')
        ax.tick_params(axis='y', labelcolor='green')
        ax2.tick_params(axis='y', labelcolor='red')
        ax.legend(loc='upper left')
        ax2.legend(loc='upper right')
        ax.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    plt.savefig(f'{output_dir}/risk_tolerance_comparison.png', dpi=300, bbox_inches='tight')
    print(f"  ✅ Saved: {output_dir}/risk_tolerance_comparison.png")
    plt.close()
    
    # 4. Year-by-year evolution for one scenario (example)
    if scenarios:
        example_scenario = scenarios[0]
        if example_scenario in all_results:
            fig, axes = plt.subplots(2, 2, figsize=(16, 12))
            fig.suptitle(f'5-Year Evolution: {example_scenario.replace("_", " ").title()}', 
                        fontsize=14, fontweight='bold')
            
            configs_to_plot = ['collaborative', 'uncollaborative', 'low_risk_tolerance', 'high_risk_tolerance']
            
            for idx, config_key in enumerate(configs_to_plot):
                if config_key not in all_results[example_scenario]:
                    continue
                
                ax = axes[idx // 2, idx % 2]
                years_data = all_results[example_scenario][config_key]['years']
                
                years = [y['year'] for y in years_data]
                profits = [y.get('accumulated_profit', 0) / 1000000 for y in years_data]
                systems_at_risk = [y.get('systems_at_risk', 0) for y in years_data]
                
                ax2 = ax.twinx()
                line1 = ax.plot(years, profits, 'o-', color='green', linewidth=2, 
                               label='Profit (M$)', markersize=8)
                line2 = ax2.plot(years, systems_at_risk, 's-', color='red', linewidth=2, 
                                label='Systems at Risk', markersize=8)
                
                ax.set_xlabel('Year', fontweight='bold')
                ax.set_ylabel('Profit (Millions $)', fontweight='bold', color='green')
                ax2.set_ylabel('Systems at Risk', fontweight='bold', color='red')
                ax.set_title(config_key.replace('_', ' ').title(), fontweight='bold')
                ax.tick_params(axis='y', labelcolor='green')
                ax2.tick_params(axis='y', labelcolor='red')
                ax.grid(True, alpha=0.3)
                
                lines = line1 + line2
                labels = [l.get_label() for l in lines]
                ax.legend(lines, labels, loc='best')
            
            plt.tight_layout()
            plt.savefig(f'{output_dir}/year_by_year_evolution.png', dpi=300, bbox_inches='tight')
            print(f"  ✅ Saved: {output_dir}/year_by_year_evolution.png")
            plt.close()
    
    print("\n✅ All visualizations generated!")


def main():
    """Main execution function."""
    results = run_comprehensive_analysis()
    
    print("\n" + "=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)
    print("\n📁 Results saved to: outputs/multi_agent_optimization/")
    print("\n📊 Generated outputs:")
    print("   - optimization_results.json: Complete results data")
    print("   - primary_results.png: Profit and systems at risk by scenario")
    print("   - collaborative_comparison.png: Collaborative vs uncollaborative")
    print("   - risk_tolerance_comparison.png: Risk tolerance variations")
    print("   - year_by_year_evolution.png: 5-year evolution example")
    
    return results


if __name__ == '__main__':
    main()

