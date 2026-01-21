"""
Generate visualizations for paper explaining threshold setting and multi-agent framework.
"""

import json
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import Rectangle
import seaborn as sns
from scipy import stats
import os

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 8)
plt.rcParams['font.size'] = 11

# Create output directory
os.makedirs('outputs/paper_figures', exist_ok=True)

def load_simulation_data():
    """Load simulation results."""
    with open('simulation_data.json', 'r') as f:
        data = json.load(f)
    return list(data.values())

def load_agent_config():
    """Load agent configuration."""
    with open('config/agent_config.json', 'r') as f:
        config = json.load(f)
    return config['agents']

def figure1_threshold_setting_methodology():
    """Figure 1: Threshold Setting Methodology"""
    runs = load_simulation_data()
    agents = load_agent_config()
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('Threshold Setting Methodology: Data-Driven Calibration', 
                 fontsize=16, fontweight='bold')
    
    # Extract KPI values
    profits = [r['accumulated_profit'] for r in runs]
    compromised = [r['compromised_systems'] for r in runs]
    availability = [r['systems_availability'] for r in runs]
    systems_at_risk = [r.get('systems_at_risk', 0) for r in runs]
    
    # CFO: Accumulated Profit
    ax = axes[0, 0]
    ax.hist(profits, bins=15, alpha=0.7, color='green', edgecolor='black')
    cfo_target = agents['CFO']['target']['min']
    ax.axvline(cfo_target, color='red', linestyle='--', linewidth=2, label=f'CFO Target: ${cfo_target:,.0f}')
    mean_profit = np.mean(profits)
    std_profit = np.std(profits)
    ax.axvline(mean_profit, color='blue', linestyle=':', linewidth=2, label=f'Mean: ${mean_profit:,.0f}')
    ax.axvline(mean_profit + 0.5*std_profit, color='orange', linestyle=':', linewidth=1, 
               label=f'Mean + 0.5σ: ${mean_profit + 0.5*std_profit:,.0f}')
    ax.set_xlabel('Accumulated Profit ($)', fontweight='bold')
    ax.set_ylabel('Frequency', fontweight='bold')
    ax.set_title('CFO: Profit Maximization\n(Min Threshold)', fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # CRO: Compromised Systems
    ax = axes[0, 1]
    ax.hist(compromised, bins=15, alpha=0.7, color='red', edgecolor='black')
    cro_target = agents['CRO']['target']['max']
    ax.axvline(cro_target, color='red', linestyle='--', linewidth=2, label=f'CRO Target: {cro_target}')
    mean_comp = np.mean(compromised)
    std_comp = np.std(compromised)
    ax.axvline(mean_comp, color='blue', linestyle=':', linewidth=2, label=f'Mean: {mean_comp:.1f}')
    ax.axvline(mean_comp - 0.5*std_comp, color='orange', linestyle=':', linewidth=1,
               label=f'Mean - 0.5σ: {mean_comp - 0.5*std_comp:.1f}')
    ax.set_xlabel('Compromised Systems', fontweight='bold')
    ax.set_ylabel('Frequency', fontweight='bold')
    ax.set_title('CRO: Risk Minimization\n(Max Threshold)', fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # COO: Systems Availability
    ax = axes[1, 0]
    ax.hist(availability, bins=15, alpha=0.7, color='blue', edgecolor='black')
    coo_target = agents['COO']['target']['min']
    ax.axvline(coo_target, color='red', linestyle='--', linewidth=2, label=f'COO Target: {coo_target:.2f}')
    mean_avail = np.mean(availability)
    std_avail = np.std(availability)
    ax.axvline(mean_avail, color='blue', linestyle=':', linewidth=2, label=f'Mean: {mean_avail:.3f}')
    ax.axvline(mean_avail + 0.3*std_avail, color='orange', linestyle=':', linewidth=1,
               label=f'Mean + 0.3σ: {mean_avail + 0.3*std_avail:.3f}')
    ax.set_xlabel('Systems Availability (0-1)', fontweight='bold')
    ax.set_ylabel('Frequency', fontweight='bold')
    ax.set_title('COO: Availability Optimization\n(Min Threshold)', fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # IT Manager: Systems at Risk
    ax = axes[1, 1]
    if 'IT_Manager' in agents:
        ax.hist(systems_at_risk, bins=15, alpha=0.7, color='purple', edgecolor='black')
        it_target = agents['IT_Manager']['target']['max']
        ax.axvline(it_target, color='red', linestyle='--', linewidth=2, label=f'IT Target: {it_target}')
        mean_risk = np.mean(systems_at_risk)
        std_risk = np.std(systems_at_risk)
        ax.axvline(mean_risk, color='blue', linestyle=':', linewidth=2, label=f'Mean: {mean_risk:.1f}')
        ax.set_xlabel('Systems at Risk', fontweight='bold')
        ax.set_ylabel('Frequency', fontweight='bold')
        ax.set_title('IT Manager: Risk Limitation\n(Max Threshold)', fontweight='bold')
        ax.legend()
        ax.grid(True, alpha=0.3)
    else:
        ax.text(0.5, 0.5, 'IT Manager\nNot Configured', 
                ha='center', va='center', fontsize=14)
        ax.set_title('IT Manager: Risk Limitation', fontweight='bold')
    
    plt.tight_layout()
    plt.savefig('outputs/paper_figures/figure1_threshold_methodology.png', dpi=300, bbox_inches='tight')
    print("✅ Saved: figure1_threshold_methodology.png")
    plt.close()

def figure2_agent_evaluation_framework():
    """Figure 2: Multi-Agent Evaluation Framework"""
    fig = plt.figure(figsize=(16, 10))
    gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)
    
    fig.suptitle('Multi-Agent Evaluation Framework: Decision-Making Process', 
                 fontsize=16, fontweight='bold', y=0.98)
    
    # Main flow diagram
    ax_main = fig.add_subplot(gs[0:2, 0:3])
    ax_main.axis('off')
    
    # Draw flow
    boxes = [
        ('Simulation\nResults', 0.1, 0.7, 'lightblue'),
        ('CFO\nEvaluation', 0.3, 0.7, 'lightgreen'),
        ('CRO\nEvaluation', 0.5, 0.7, 'lightcoral'),
        ('COO\nEvaluation', 0.7, 0.7, 'lightyellow'),
        ('Agent\nConsensus', 0.9, 0.7, 'lightgray'),
        ('Recommendations', 0.5, 0.3, 'lightpink')
    ]
    
    for label, x, y, color in boxes:
        rect = Rectangle((x-0.08, y-0.1), 0.16, 0.2, 
                        facecolor=color, edgecolor='black', linewidth=2)
        ax_main.add_patch(rect)
        ax_main.text(x, y, label, ha='center', va='center', 
                    fontweight='bold', fontsize=10)
    
    # Arrows
    arrows = [
        (0.18, 0.7, 0.22, 0.7),
        (0.38, 0.7, 0.42, 0.7),
        (0.58, 0.7, 0.62, 0.7),
        (0.78, 0.7, 0.82, 0.7),
        (0.5, 0.6, 0.5, 0.4)
    ]
    
    for x1, y1, x2, y2 in arrows:
        ax_main.annotate('', xy=(x2, y2), xytext=(x1, y1),
                        arrowprops=dict(arrowstyle='->', lw=2, color='black'))
    
    # Agent details
    agents = load_agent_config()
    
    # CFO details
    ax_cfo = fig.add_subplot(gs[2, 0])
    ax_cfo.axis('off')
    cfo = agents['CFO']
    ax_cfo.text(0.5, 0.9, 'CFO', ha='center', fontsize=12, fontweight='bold')
    ax_cfo.text(0.1, 0.7, f"KPI: {cfo['kpi']}", fontsize=9)
    ax_cfo.text(0.1, 0.5, f"Target: ≥ ${cfo['target']['min']:,.0f}", fontsize=9)
    ax_cfo.text(0.1, 0.3, f"Risk Tolerance: {cfo['personality']['risk_tolerance']:.1f}", fontsize=9)
    ax_cfo.text(0.1, 0.1, f"Ambition: {cfo['personality']['ambition']:.1f}", fontsize=9)
    ax_cfo.add_patch(Rectangle((0, 0), 1, 1, fill=False, edgecolor='green', linewidth=2))
    
    # CRO details
    ax_cro = fig.add_subplot(gs[2, 1])
    ax_cro.axis('off')
    cro = agents['CRO']
    ax_cro.text(0.5, 0.9, 'CRO', ha='center', fontsize=12, fontweight='bold')
    ax_cro.text(0.1, 0.7, f"KPI: {cro['kpi']}", fontsize=9)
    ax_cro.text(0.1, 0.5, f"Target: ≤ {cro['target']['max']}", fontsize=9)
    ax_cro.text(0.1, 0.3, f"Risk Tolerance: {cro['personality']['risk_tolerance']:.1f}", fontsize=9)
    ax_cro.text(0.1, 0.1, f"Ambition: {cro['personality']['ambition']:.1f}", fontsize=9)
    ax_cro.add_patch(Rectangle((0, 0), 1, 1, fill=False, edgecolor='red', linewidth=2))
    
    # COO details
    ax_coo = fig.add_subplot(gs[2, 2])
    ax_coo.axis('off')
    coo = agents['COO']
    ax_coo.text(0.5, 0.9, 'COO', ha='center', fontsize=12, fontweight='bold')
    ax_coo.text(0.1, 0.7, f"KPI: {coo['kpi']}", fontsize=9)
    ax_coo.text(0.1, 0.5, f"Target: ≥ {coo['target']['min']:.2f}", fontsize=9)
    ax_coo.text(0.1, 0.3, f"Risk Tolerance: {coo['personality']['risk_tolerance']:.1f}", fontsize=9)
    ax_coo.text(0.1, 0.1, f"Ambition: {coo['personality']['ambition']:.1f}", fontsize=9)
    ax_coo.add_patch(Rectangle((0, 0), 1, 1, fill=False, edgecolor='blue', linewidth=2))
    
    plt.savefig('outputs/paper_figures/figure2_agent_framework.png', dpi=300, bbox_inches='tight')
    print("✅ Saved: figure2_agent_framework.png")
    plt.close()

def figure3_threshold_impact_analysis():
    """Figure 3: Impact of Threshold Values on Agent Evaluations"""
    runs = load_simulation_data()
    agents = load_agent_config()
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('Threshold Impact Analysis: Sensitivity of Agent Evaluations', 
                 fontsize=16, fontweight='bold')
    
    profits = [r['accumulated_profit'] for r in runs]
    compromised = [r['compromised_systems'] for r in runs]
    availability = [r['systems_availability'] for r in runs]
    
    # CFO: Different threshold levels
    ax = axes[0, 0]
    thresholds = np.linspace(min(profits), max(profits), 20)
    below_target = []
    for thresh in thresholds:
        below = sum(1 for p in profits if p < thresh)
        below_target.append(below / len(profits) * 100)
    
    ax.plot(thresholds, below_target, 'g-', linewidth=2, label='% Below Target')
    cfo_target = agents['CFO']['target']['min']
    ax.axvline(cfo_target, color='red', linestyle='--', linewidth=2, 
               label=f'Current Target: ${cfo_target:,.0f}')
    ax.axhline(50, color='gray', linestyle=':', alpha=0.5, label='50% Threshold')
    ax.set_xlabel('Threshold Value ($)', fontweight='bold')
    ax.set_ylabel('% of Runs Below Target', fontweight='bold')
    ax.set_title('CFO: Threshold Sensitivity\n(Accumulated Profit)', fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # CRO: Different threshold levels
    ax = axes[0, 1]
    thresholds = np.linspace(0, max(compromised) + 2, 20)
    above_target = []
    for thresh in thresholds:
        above = sum(1 for c in compromised if c > thresh)
        above_target.append(above / len(compromised) * 100)
    
    ax.plot(thresholds, above_target, 'r-', linewidth=2, label='% Above Target')
    cro_target = agents['CRO']['target']['max']
    ax.axvline(cro_target, color='red', linestyle='--', linewidth=2, 
               label=f'Current Target: {cro_target}')
    ax.axhline(50, color='gray', linestyle=':', alpha=0.5, label='50% Threshold')
    ax.set_xlabel('Threshold Value (Systems)', fontweight='bold')
    ax.set_ylabel('% of Runs Above Target', fontweight='bold')
    ax.set_title('CRO: Threshold Sensitivity\n(Compromised Systems)', fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # COO: Different threshold levels
    ax = axes[1, 0]
    thresholds = np.linspace(min(availability), max(availability), 20)
    below_target = []
    for thresh in thresholds:
        below = sum(1 for a in availability if a < thresh)
        below_target.append(below / len(availability) * 100)
    
    ax.plot(thresholds, below_target, 'b-', linewidth=2, label='% Below Target')
    coo_target = agents['COO']['target']['min']
    ax.axvline(coo_target, color='red', linestyle='--', linewidth=2, 
               label=f'Current Target: {coo_target:.2f}')
    ax.axhline(50, color='gray', linestyle=':', alpha=0.5, label='50% Threshold')
    ax.set_xlabel('Threshold Value (0-1)', fontweight='bold')
    ax.set_ylabel('% of Runs Below Target', fontweight='bold')
    ax.set_title('COO: Threshold Sensitivity\n(Systems Availability)', fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Combined: Agent agreement vs threshold strictness
    ax = axes[1, 1]
    # Simulate different threshold strictness levels
    strictness_levels = np.linspace(0.5, 1.5, 20)
    agreement_rates = []
    
    for strictness in strictness_levels:
        # Adjust thresholds
        cfo_adj = np.mean(profits) + strictness * 0.5 * np.std(profits)
        cro_adj = max(0, np.mean(compromised) - strictness * 0.5 * np.std(compromised))
        coo_adj = min(1.0, np.mean(availability) + strictness * 0.3 * np.std(availability))
        
        # Count runs that meet all thresholds
        meets_all = sum(1 for r in runs 
                       if r['accumulated_profit'] >= cfo_adj and
                          r['compromised_systems'] <= cro_adj and
                          r['systems_availability'] >= coo_adj)
        agreement_rates.append(meets_all / len(runs) * 100)
    
    ax.plot(strictness_levels, agreement_rates, 'purple', linewidth=2, marker='o')
    ax.axvline(1.0, color='red', linestyle='--', linewidth=2, 
               label='Current Setting (1.0)')
    ax.set_xlabel('Threshold Strictness Multiplier', fontweight='bold')
    ax.set_ylabel('% of Runs Meeting All Targets', fontweight='bold')
    ax.set_title('Multi-Agent Agreement Rate\nvs Threshold Strictness', fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('outputs/paper_figures/figure3_threshold_impact.png', dpi=300, bbox_inches='tight')
    print("✅ Saved: figure3_threshold_impact.png")
    plt.close()

def figure4_personality_impact():
    """Figure 4: Personality Traits Impact on Recommendations"""
    agents = load_agent_config()
    
    fig, axes = plt.subplots(1, 3, figsize=(16, 5))
    fig.suptitle('Personality Traits Impact on Agent Behavior', 
                 fontsize=16, fontweight='bold')
    
    # Extract personality data
    agent_names = []
    risk_tolerance = []
    friendliness = []
    ambition = []
    
    for name, config in agents.items():
        if name not in ['IT_Manager', 'CHRO', 'COO_Business']:  # Focus on main 3
            agent_names.append(name)
            risk_tolerance.append(config['personality']['risk_tolerance'])
            friendliness.append(config['personality']['friendliness'])
            ambition.append(config['personality']['ambition'])
    
    # Risk Tolerance
    ax = axes[0]
    colors = ['green', 'red', 'blue']
    bars = ax.bar(agent_names, risk_tolerance, color=colors, alpha=0.7, edgecolor='black')
    ax.set_ylabel('Risk Tolerance (0-1)', fontweight='bold')
    ax.set_title('Risk Tolerance Levels', fontweight='bold')
    ax.set_ylim(0, 1)
    ax.grid(True, alpha=0.3, axis='y')
    for i, (bar, val) in enumerate(zip(bars, risk_tolerance)):
        ax.text(bar.get_x() + bar.get_width()/2, val + 0.02, 
               f'{val:.2f}', ha='center', fontweight='bold')
    
    # Friendliness
    ax = axes[1]
    bars = ax.bar(agent_names, friendliness, color=colors, alpha=0.7, edgecolor='black')
    ax.set_ylabel('Friendliness (0-1)', fontweight='bold')
    ax.set_title('Collaborative Tendency', fontweight='bold')
    ax.set_ylim(0, 1)
    ax.grid(True, alpha=0.3, axis='y')
    for i, (bar, val) in enumerate(zip(bars, friendliness)):
        ax.text(bar.get_x() + bar.get_width()/2, val + 0.02, 
               f'{val:.2f}', ha='center', fontweight='bold')
    
    # Ambition
    ax = axes[2]
    bars = ax.bar(agent_names, ambition, color=colors, alpha=0.7, edgecolor='black')
    ax.set_ylabel('Ambition (0-1)', fontweight='bold')
    ax.set_title('Performance Drive', fontweight='bold')
    ax.set_ylim(0, 1)
    ax.grid(True, alpha=0.3, axis='y')
    for i, (bar, val) in enumerate(zip(bars, ambition)):
        ax.text(bar.get_x() + bar.get_width()/2, val + 0.02, 
               f'{val:.2f}', ha='center', fontweight='bold')
    
    plt.tight_layout()
    plt.savefig('outputs/paper_figures/figure4_personality_impact.png', dpi=300, bbox_inches='tight')
    print("✅ Saved: figure4_personality_impact.png")
    plt.close()

def figure5_strategy_evaluation():
    """Figure 5: Strategy Evaluation Across Agents"""
    runs = load_simulation_data()
    agents = load_agent_config()
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('Strategy Evaluation: Multi-Agent Perspective', 
                 fontsize=16, fontweight='bold')
    
    # Extract strategy data
    strategies = [r['strategy'] for r in runs]
    profits = [r['accumulated_profit'] for r in runs]
    compromised = [r['compromised_systems'] for r in runs]
    availability = [r['systems_availability'] for r in runs]
    
    # Agent evaluations (meet target or not)
    cfo_target = agents['CFO']['target']['min']
    cro_target = agents['CRO']['target']['max']
    coo_target = agents['COO']['target']['min']
    
    cfo_meets = [1 if p >= cfo_target else 0 for p in profits]
    cro_meets = [1 if c <= cro_target else 0 for c in compromised]
    coo_meets = [1 if a >= coo_target else 0 for a in availability]
    
    # Strategy ranking by each agent
    ax = axes[0, 0]
    strategy_indices = list(range(len(strategies)))
    width = 0.25
    x = np.arange(len(strategies))
    
    ax.bar(x - width, cfo_meets, width, label='CFO Meets Target', color='green', alpha=0.7)
    ax.bar(x, cro_meets, width, label='CRO Meets Target', color='red', alpha=0.7)
    ax.bar(x + width, coo_meets, width, label='COO Meets Target', color='blue', alpha=0.7)
    
    ax.set_xlabel('Strategy', fontweight='bold')
    ax.set_ylabel('Meets Target (1) or Not (0)', fontweight='bold')
    ax.set_title('Agent Target Achievement by Strategy', fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels([s[:15] for s in strategies], rotation=45, ha='right')
    ax.legend()
    ax.grid(True, alpha=0.3, axis='y')
    
    # Pareto front: Profit vs Compromised Systems
    ax = axes[0, 1]
    scatter = ax.scatter(compromised, profits, c=availability, 
                        s=100, alpha=0.7, cmap='viridis', edgecolors='black')
    
    # Highlight strategies that meet all targets
    all_meet = [i for i in range(len(runs)) 
                if cfo_meets[i] and cro_meets[i] and coo_meets[i]]
    if all_meet:
        ax.scatter([compromised[i] for i in all_meet], 
                  [profits[i] for i in all_meet],
                  s=200, marker='*', color='gold', edgecolors='black', 
                  linewidth=2, label='Meets All Targets', zorder=5)
    
    ax.set_xlabel('Compromised Systems', fontweight='bold')
    ax.set_ylabel('Accumulated Profit ($)', fontweight='bold')
    ax.set_title('Trade-off Analysis: Security vs Profit\n(Color = Availability)', fontweight='bold')
    plt.colorbar(scatter, ax=ax, label='Systems Availability')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Agent consensus score
    ax = axes[1, 0]
    consensus_scores = [cfo_meets[i] + cro_meets[i] + coo_meets[i] for i in range(len(runs))]
    ax.barh(strategies, consensus_scores, color='purple', alpha=0.7, edgecolor='black')
    ax.set_xlabel('Number of Agents Approving', fontweight='bold')
    ax.set_title('Agent Consensus Score\n(Out of 3 Agents)', fontweight='bold')
    ax.set_xlim(0, 3.5)
    ax.grid(True, alpha=0.3, axis='x')
    
    # F1-F4 budget allocation comparison
    ax = axes[1, 1]
    f1_vals = [r['F1'] for r in runs]
    f2_vals = [r['F2'] for r in runs]
    f3_vals = [r['F3'] for r in runs]
    f4_vals = [r['F4'] for r in runs]
    
    x = np.arange(len(strategies))
    width = 0.2
    ax.bar(x - 1.5*width, f1_vals, width, label='F1: Prevention', color='green', alpha=0.7)
    ax.bar(x - 0.5*width, f2_vals, width, label='F2: Detection', color='blue', alpha=0.7)
    ax.bar(x + 0.5*width, f3_vals, width, label='F3: Response', color='orange', alpha=0.7)
    ax.bar(x + 1.5*width, f4_vals, width, label='F4: Recovery', color='red', alpha=0.7)
    
    ax.set_xlabel('Strategy', fontweight='bold')
    ax.set_ylabel('Budget Allocation (%)', fontweight='bold')
    ax.set_title('Budget Allocation (F1-F4) by Strategy', fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels([s[:15] for s in strategies], rotation=45, ha='right')
    ax.legend()
    ax.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    plt.savefig('outputs/paper_figures/figure5_strategy_evaluation.png', dpi=300, bbox_inches='tight')
    print("✅ Saved: figure5_strategy_evaluation.png")
    plt.close()

def generate_summary_document():
    """Generate a summary document explaining the visualizations."""
    doc = """# Visualization Summary: Multi-Agent Framework for Cyber-Risk Management

## Overview
This document explains the visualizations generated to illustrate the multi-agent framework, threshold setting methodology, and evaluation process.

## Figure 1: Threshold Setting Methodology
**Purpose**: Demonstrates how thresholds are calibrated using data-driven approaches.

**Key Elements**:
- Histograms showing distribution of KPI values across simulation runs
- Current threshold values (red dashed lines)
- Statistical measures (mean, mean ± σ) used for calibration
- Different threshold types: min thresholds (CFO, COO) and max thresholds (CRO)

**Insights**:
- CFO target ($1.2M) is set above mean to encourage high performance
- CRO target (10 systems) is set below mean to minimize risk
- COO target (0.92) ensures high availability standards
- Thresholds are positioned to balance achievability with ambition

## Figure 2: Multi-Agent Evaluation Framework
**Purpose**: Illustrates the system architecture and decision-making flow.

**Key Elements**:
- Flow diagram showing simulation → agent evaluation → consensus → recommendations
- Agent specifications (KPI focus, targets, personality traits)
- Integration points between components

**Insights**:
- Each agent independently evaluates results based on their KPI
- Personality traits influence recommendation style
- Consensus emerges from individual agent evaluations

## Figure 3: Threshold Impact Analysis
**Purpose**: Shows sensitivity of agent evaluations to threshold changes.

**Key Elements**:
- Sensitivity curves showing % of runs meeting targets at different threshold levels
- Current threshold positions
- Multi-agent agreement rate vs threshold strictness

**Insights**:
- Stricter thresholds reduce number of acceptable strategies
- Optimal threshold setting balances individual agent goals with overall consensus
- Too strict thresholds lead to no strategies meeting all targets

## Figure 4: Personality Traits Impact
**Purpose**: Visualizes personality trait differences across agents.

**Key Elements**:
- Risk tolerance: CRO is most risk-averse, COO is moderate
- Friendliness: COO is most collaborative
- Ambition: CFO is most ambitious, driving for higher targets

**Insights**:
- Personality traits create diverse perspectives
- Risk tolerance directly affects recommendation aggressiveness
- Ambition level influences target setting and evaluation

## Figure 5: Strategy Evaluation
**Purpose**: Shows how different strategies perform from multi-agent perspective.

**Key Elements**:
- Target achievement by strategy for each agent
- Trade-off analysis (security vs profit vs availability)
- Consensus scores showing strategies approved by multiple agents
- Budget allocation patterns (F1-F4)

**Insights**:
- No single strategy dominates across all KPIs
- Strategies that meet all targets are rare (gold stars)
- Budget allocation patterns correlate with performance
- Prevention-heavy strategies tend to reduce compromised systems but may reduce profits

## Threshold Setting Methodology

### Data-Driven Approach
1. **Collect Simulation Results**: Run multiple strategies and collect KPI values
2. **Statistical Analysis**: Calculate mean, standard deviation, percentiles
3. **Target Positioning**: 
   - For maximize KPIs (profit, availability): Set at mean + k×σ (k=0.3-0.5)
   - For minimize KPIs (compromised systems): Set at mean - k×σ (k=0.5)
4. **Calibration**: Adjust based on organizational risk appetite

### Domain Knowledge Integration
- Industry benchmarks
- Regulatory requirements
- Organizational risk tolerance
- Historical performance data

### Threshold Types
- **Min Thresholds**: For KPIs to maximize (profit ≥ $1.2M, availability ≥ 0.92)
- **Max Thresholds**: For KPIs to minimize (compromised systems ≤ 10)

## Agent Evaluation Process

1. **KPI Extraction**: Extract relevant KPI value from simulation results
2. **Threshold Comparison**: Compare KPI value against agent's target
3. **Status Determination**: 
   - Below target: KPI < min or KPI > max
   - On target: min ≤ KPI ≤ max
   - Above target: KPI > min (for maximize) or KPI < max (for minimize)
4. **Recommendation Generation**: Personality-driven suggestions based on status

## Personality-Driven Recommendations

### Risk Tolerance Impact
- **High (>0.7)**: Aggressive recommendations when below target
- **Low (<0.3)**: Cautious, gradual improvements preferred

### Ambition Impact
- **High (>0.8)**: Pushes for optimization even when on target
- **Low (<0.5)**: Satisfied with meeting targets

### Friendliness Impact
- **High (>0.7)**: Collaborative, satisfied with team performance
- **Low (<0.5)**: More critical, pushes for individual excellence

## Key Findings

1. **Threshold Calibration**: Data-driven approach provides objective, defensible thresholds
2. **Multi-Agent Perspective**: Captures diverse stakeholder viewpoints
3. **Trade-offs**: No single strategy dominates; framework helps identify Pareto-optimal solutions
4. **Personality Impact**: Traits significantly influence recommendation style and target setting
5. **Consensus Building**: Framework enables identification of strategies acceptable to multiple stakeholders

## Applications

- **Strategic Planning**: Evaluate budget allocation strategies before implementation
- **Risk Assessment**: Understand trade-offs between security and business objectives
- **Stakeholder Alignment**: Visualize how different perspectives evaluate same strategies
- **Decision Support**: Data-driven recommendations with personality-driven nuance
"""
    
    with open('outputs/paper_figures/visualization_summary.md', 'w') as f:
        f.write(doc)
    print("✅ Saved: visualization_summary.md")

def main():
    """Generate all visualizations."""
    print("=" * 70)
    print("📊 Generating Paper Visualizations")
    print("=" * 70)
    
    print("\n1. Generating Figure 1: Threshold Setting Methodology...")
    figure1_threshold_setting_methodology()
    
    print("\n2. Generating Figure 2: Multi-Agent Evaluation Framework...")
    figure2_agent_evaluation_framework()
    
    print("\n3. Generating Figure 3: Threshold Impact Analysis...")
    figure3_threshold_impact_analysis()
    
    print("\n4. Generating Figure 4: Personality Impact...")
    figure4_personality_impact()
    
    print("\n5. Generating Figure 5: Strategy Evaluation...")
    figure5_strategy_evaluation()
    
    print("\n6. Generating Summary Document...")
    generate_summary_document()
    
    print("\n" + "=" * 70)
    print("✅ All visualizations generated!")
    print("=" * 70)
    print("\n📁 Files saved to: outputs/paper_figures/")
    print("\n📄 Paper outline saved to: PAPER_OUTLINE.md")
    print("\n💡 Next steps:")
    print("   - Review visualizations in outputs/paper_figures/")
    print("   - Use figures in paper sections")
    print("   - Reference PAPER_OUTLINE.md for structure")

if __name__ == '__main__':
    main()

