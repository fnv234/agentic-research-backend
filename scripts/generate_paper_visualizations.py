"""
Generate visualizations for paper explaining threshold setting and multi-agent framework.
Uses 5 agents (CFO, CRO, COO, IT_Manager, CHRO) consistent with optimization and config.
"""

import json
import os
import sys

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import Rectangle
import seaborn as sns
from scipy import stats

# Run from repo root so app is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 8)
plt.rcParams['font.size'] = 11

# Create output directory
os.makedirs('outputs/paper_figures', exist_ok=True)

def load_simulation_data():
    """Load simulation results from simulation_data.json, or fallback to optimization_results / sim_data."""
    if os.path.exists('simulation_data.json'):
        with open('simulation_data.json', 'r') as f:
            data = json.load(f)
        runs = list(data.values()) if isinstance(data, dict) else data
        if runs and isinstance(runs[0], dict) and 'accumulated_profit' in runs[0]:
            return runs
    # Fallback: build from optimization results (first scenario, first config, years)
    opt_path = 'outputs/multi_agent_optimization/optimization_results.json'
    if os.path.exists(opt_path):
        with open(opt_path, 'r') as f:
            opt = json.load(f)
        runs = []
        for scenario, configs in opt.items():
            for config_name, config_data in configs.items():
                for y in config_data.get('years_summary', [])[:5]:
                    comp = float(y.get('compromised', 0) or 0)
                    profit = float(y.get('profit', 0) or 0)
                    risk = float(y.get('systems_at_risk', 0) or 0)
                    runs.append({
                        'accumulated_profit': profit,
                        'compromised_systems': comp,
                        'systems_availability': min(1.0, max(0, 1.0 - comp / 100)),
                        'systems_at_risk': risk,
                        'strategy': f"{scenario}_{config_name}_y{y.get('year', 0)}",
                        'F1': float(y.get('F1', 25) or 25), 'F2': float(y.get('F2', 25) or 25),
                        'F3': float(y.get('F3', 25) or 25), 'F4': float(y.get('F4', 25) or 25)
                    })
        if runs:
            return runs
    # Fallback: minimal from sim_data.csv if present
    csv_path = 'data/sim_data.csv'
    if os.path.exists(csv_path):
        import pandas as pd
        df = pd.read_csv(csv_path)
        if 'Cum. Profits' in df.columns:
            df['Cum. Profits'] = pd.to_numeric(df['Cum. Profits'].astype(str).str.replace(',', ''), errors='coerce')
        runs = []
        for i, row in df.head(50).iterrows():
            raw_profit = row.get('Cum. Profits', 0)
            profit = (float(raw_profit) * 1000) if raw_profit is not None and str(raw_profit).strip() else 0
            comp = float(row.get('Comp. Systems', 0) or 0)
            runs.append({
                'accumulated_profit': profit,
                'compromised_systems': comp,
                'systems_availability': max(0, min(1.0, 1.0 - comp / 100)),
                'systems_at_risk': max(0, comp + 5),
                'strategy': f"Run_{i+1}",
                'F1': 30, 'F2': 30, 'F3': 25, 'F4': 15
            })
        return runs
    raise FileNotFoundError("No simulation_data.json, optimization_results.json, or data/sim_data.csv found. Run multi_agent_optimization.py or generate_dashboard_data.py first.")

def load_agent_config():
    """Load agent configuration from config file or app default (5 agents)."""
    config_path = 'config/agent_config.json'
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            config = json.load(f)
        return config.get('agents', config)
    from app.agents import load_agent_config as app_load
    return app_load()

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
    print("Saved figure1_threshold_methodology.png")
    plt.close()

def figure2_agent_evaluation_framework():
    """Figure 2: Multi-Agent Evaluation Framework (5 agents)"""
    agents = load_agent_config()
    agent_names = [a for a in ['CFO', 'CRO', 'COO', 'IT_Manager', 'CHRO'] if a in agents]
    n_agents = len(agent_names)
    if n_agents == 0:
        agent_names = list(agents.keys())[:5]
        n_agents = len(agent_names)

    fig = plt.figure(figsize=(16, 10))
    n_cols = min(5, n_agents)
    gs = fig.add_gridspec(3, n_cols, hspace=0.35, wspace=0.25)
    fig.suptitle('Multi-Agent Evaluation Framework: Decision-Making Process (5 Agents)', 
                 fontsize=16, fontweight='bold', y=0.98)

    ax_main = fig.add_subplot(gs[0:2, :])
    ax_main.axis('off')
    ax_main.set_xlim(0, 1)
    ax_main.set_ylim(0, 1)
    # Fixed positions so all boxes fit (Consensus not cut off): 7 top boxes in [0.06, 0.88]
    n_top = n_agents + 2  # Simulation + agents + Consensus
    xs = np.linspace(0.06, 0.88, n_top)
    box_w = 0.10
    colors_flow = ['lightblue', 'lightgreen', 'lightcoral', 'lightyellow', 'lavender', 'lavender', 'lightgray']
    boxes = [('Simulation\nResults', xs[0], 0.7, colors_flow[0])]
    for i, name in enumerate(agent_names):
        boxes.append((f'{name}\nEval', xs[i + 1], 0.7, colors_flow[(i + 1) % len(colors_flow)]))
    boxes.append(('Agent\nConsensus', xs[n_top - 1], 0.7, 'lightgray'))
    boxes.append(('Recommendations', 0.5, 0.3, 'lightpink'))
    for label, x, y, color in boxes:
        w = box_w if 'Recommendations' not in label else 0.18
        h = 0.18 if 'Recommendations' not in label else 0.14
        rect = Rectangle((x - w/2, y - h/2), w, h, facecolor=color, edgecolor='black', linewidth=2)
        ax_main.add_patch(rect)
        ax_main.text(x, y, label, ha='center', va='center', fontweight='bold', fontsize=8)
    for i in range(n_top - 1):
        ax_main.annotate('', xy=(xs[i + 1] - box_w/2 - 0.01, 0.7), xytext=(xs[i] + box_w/2 + 0.01, 0.7),
                         arrowprops=dict(arrowstyle='->', lw=2, color='black'))
    ax_main.annotate('', xy=(0.5, 0.39), xytext=(0.5, 0.61),
                     arrowprops=dict(arrowstyle='->', lw=2, color='black'))

    # Agent detail panels (5 agents)
    colors = ['green', 'red', 'blue', 'purple', 'orange']
    for idx, name in enumerate(agent_names[:5]):
        ax = fig.add_subplot(gs[2, idx % n_cols])
        ax.axis('off')
        a = agents[name]
        ax.text(0.5, 0.9, name, ha='center', fontsize=11, fontweight='bold')
        ax.text(0.1, 0.65, f"KPI: {a['kpi']}", fontsize=8)
        t = a.get('target', {})
        if 'min' in t:
            ax.text(0.1, 0.45, f"Target: ≥ {t['min']:,.0f}" if t['min'] > 100 else f"Target: ≥ {t['min']:.2f}", fontsize=8)
        else:
            ax.text(0.1, 0.45, f"Target: ≤ {t.get('max', '')}", fontsize=8)
        ax.text(0.1, 0.25, f"Risk Tol: {a['personality']['risk_tolerance']:.2f}", fontsize=8)
        ax.text(0.1, 0.05, f"Ambition: {a['personality']['ambition']:.2f}", fontsize=8)
        ax.add_patch(Rectangle((0, 0), 1, 1, fill=False, edgecolor=colors[idx % len(colors)], linewidth=2))

    plt.savefig('outputs/paper_figures/figure2_agent_framework_example.png', dpi=300, bbox_inches='tight')
    print("Saved figure2_agent_framework_example.png")
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
    
    # Combined: Agent agreement vs threshold strictness (5 agents when in config)
    ax = axes[1, 1]
    strictness_levels = np.linspace(0.5, 1.5, 20)
    agreement_rates = []
    n_agents = 3
    if 'IT_Manager' in agents:
        it_target = agents['IT_Manager']['target'].get('max', 8)
        n_agents += 1
    if 'CHRO' in agents:
        chro_target = agents['CHRO']['target'].get('min', 0.93)
        n_agents += 1
    def run_meets_all(r, cfo_adj, cro_adj, coo_adj):
        if not (r['accumulated_profit'] >= cfo_adj and r['compromised_systems'] <= cro_adj and r['systems_availability'] >= coo_adj):
            return False
        if 'IT_Manager' in agents and r['compromised_systems'] > agents['IT_Manager']['target'].get('max', 8):
            return False
        if 'CHRO' in agents and r['systems_availability'] < agents['CHRO']['target'].get('min', 0.93):
            return False
        return True

    for strictness in strictness_levels:
        cfo_adj = np.mean(profits) + strictness * 0.5 * np.std(profits)
        cro_adj = max(0, np.mean(compromised) - strictness * 0.5 * np.std(compromised))
        coo_adj = min(1.0, np.mean(availability) + strictness * 0.3 * np.std(availability))
        count_meets = sum(1 for r in runs if run_meets_all(r, cfo_adj, cro_adj, coo_adj))
        agreement_rates.append(count_meets / len(runs) * 100)
    
    ax.plot(strictness_levels, agreement_rates, 'purple', linewidth=2, marker='o')
    ax.axvline(1.0, color='red', linestyle='--', linewidth=2, 
               label='Current Setting (1.0)')
    ax.set_xlabel('Threshold Strictness Multiplier', fontweight='bold')
    ax.set_ylabel('% of Runs Meeting All Targets', fontweight='bold')
    ax.set_title(f'Multi-Agent Agreement Rate ({n_agents} Agents)\nvs Threshold Strictness', fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('outputs/paper_figures/figure3_threshold_impact.png', dpi=300, bbox_inches='tight')
    print("Saved figure3_threshold_impact.png")
    plt.close()

def figure4_personality_impact():
    """Figure 4: Personality Traits Impact on Recommendations (5 agents)"""
    agents = load_agent_config()
    agent_names = [a for a in ['CFO', 'CRO', 'COO', 'IT_Manager', 'CHRO'] if a in agents]
    if not agent_names:
        agent_names = list(agents.keys())
    
    fig, axes = plt.subplots(1, 3, figsize=(16, 5))
    fig.suptitle('Personality Traits Impact on Agent Behavior (5 Agents)', 
                 fontsize=16, fontweight='bold')
    
    risk_tolerance = [agents[n]['personality']['risk_tolerance'] for n in agent_names]
    friendliness = [agents[n]['personality']['friendliness'] for n in agent_names]
    ambition = [agents[n]['personality']['ambition'] for n in agent_names]
    
    bar_colors = ['green', 'red', 'blue', 'purple', 'orange'][:len(agent_names)]
    
    # Risk Tolerance
    ax = axes[0]
    bars = ax.bar(agent_names, risk_tolerance, color=bar_colors, alpha=0.7, edgecolor='black')
    ax.set_ylabel('Risk Tolerance (0-1)', fontweight='bold')
    ax.set_title('Risk Tolerance Levels', fontweight='bold')
    ax.set_ylim(0, 1)
    ax.grid(True, alpha=0.3, axis='y')
    for i, (bar, val) in enumerate(zip(bars, risk_tolerance)):
        ax.text(bar.get_x() + bar.get_width()/2, val + 0.02, 
               f'{val:.2f}', ha='center', fontweight='bold')
    
    # Friendliness
    ax = axes[1]
    bars = ax.bar(agent_names, friendliness, color=bar_colors, alpha=0.7, edgecolor='black')
    ax.set_ylabel('Friendliness (0-1)', fontweight='bold')
    ax.set_title('Collaborative Tendency', fontweight='bold')
    ax.set_ylim(0, 1)
    ax.grid(True, alpha=0.3, axis='y')
    for i, (bar, val) in enumerate(zip(bars, friendliness)):
        ax.text(bar.get_x() + bar.get_width()/2, val + 0.02, 
               f'{val:.2f}', ha='center', fontweight='bold')
    
    # Ambition
    ax = axes[2]
    bars = ax.bar(agent_names, ambition, color=bar_colors, alpha=0.7, edgecolor='black')
    ax.set_ylabel('Ambition (0-1)', fontweight='bold')
    ax.set_title('Performance Drive', fontweight='bold')
    ax.set_ylim(0, 1)
    ax.grid(True, alpha=0.3, axis='y')
    for i, (bar, val) in enumerate(zip(bars, ambition)):
        ax.text(bar.get_x() + bar.get_width()/2, val + 0.02, 
               f'{val:.2f}', ha='center', fontweight='bold')
    
    plt.tight_layout()
    plt.savefig('outputs/paper_figures/personality_comparison_three_agents.png', dpi=300, bbox_inches='tight')
    print("Saved personality_comparison_three_agents.png (5 agents)")
    plt.close()

def figure5_strategy_evaluation():
    """Figure 5: Strategy Evaluation (5 agents) – meaningful target summary, trade-off, consensus dist, budget per agent."""
    runs = load_simulation_data()
    agents = load_agent_config()
    agent_list = [a for a in ['CFO', 'CRO', 'COO', 'IT_Manager', 'CHRO'] if a in agents]
    if not agent_list:
        agent_list = list(agents.keys())
    n_ag = len(agent_list)

    profits = [r['accumulated_profit'] for r in runs]
    compromised = [r['compromised_systems'] for r in runs]
    availability = [r['systems_availability'] for r in runs]
    cfo_target = agents.get('CFO', {}).get('target', {}).get('min', 1200000)
    cro_target = agents.get('CRO', {}).get('target', {}).get('max', 10)
    coo_target = agents.get('COO', {}).get('target', {}).get('min', 0.92)
    it_target = agents.get('IT_Manager', {}).get('target', {}).get('max', 8)
    chro_target = agents.get('CHRO', {}).get('target', {}).get('min', 0.93)
    cfo_meets = [1 if p >= cfo_target else 0 for p in profits]
    cro_meets = [1 if c <= cro_target else 0 for c in compromised]
    coo_meets = [1 if a >= coo_target else 0 for a in availability]
    it_meets = [1 if c <= it_target else 0 for c in compromised]
    chro_meets = [1 if a >= chro_target else 0 for a in availability]
    consensus_scores = [cfo_meets[i] + cro_meets[i] + coo_meets[i] + it_meets[i] + chro_meets[i] for i in range(len(runs))]
    meets_list = [cfo_meets, cro_meets, coo_meets, it_meets, chro_meets]
    colors_ag = ['green', 'red', 'blue', 'purple', 'orange']

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('Strategy Evaluation: Multi-Agent Perspective (5 Agents)', fontsize=16, fontweight='bold')

    # Top-left: Share of runs meeting each agent's target (5 bars, one per agent)
    ax = axes[0, 0]
    pct_meets = [100 * np.mean(m) for m in meets_list[:n_ag]]
    bars = ax.bar(agent_list, pct_meets, color=colors_ag[:n_ag], alpha=0.7, edgecolor='black')
    ax.set_ylabel('% of Runs Meeting Target', fontweight='bold')
    ax.set_title('Target Achievement by Agent', fontweight='bold')
    ax.set_ylim(0, 105)
    ax.axhline(50, color='gray', linestyle=':', alpha=0.7)
    for bar, pct in zip(bars, pct_meets):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 2, f'{pct:.0f}%', ha='center', fontsize=9)
    ax.grid(True, alpha=0.3, axis='y')

    # Top-right: Trade-off analysis (keep as requested)
    ax = axes[0, 1]
    scatter = ax.scatter(compromised, profits, c=availability, s=80, alpha=0.7, cmap='viridis', edgecolors='black')
    all_meet = [i for i in range(len(runs)) if all(meets_list[j][i] for j in range(n_ag))]
    if all_meet:
        ax.scatter([compromised[i] for i in all_meet], [profits[i] for i in all_meet],
                   s=180, marker='*', color='gold', edgecolors='black', linewidth=2, label='Meets All Targets', zorder=5)
    ax.set_xlabel('Compromised Systems', fontweight='bold')
    ax.set_ylabel('Accumulated Profit ($)', fontweight='bold')
    ax.set_title('Trade-off: Security vs Profit\n(Color = Availability)', fontweight='bold')
    plt.colorbar(scatter, ax=ax, label='Systems Availability')
    ax.legend()
    ax.grid(True, alpha=0.3)

    # Bottom-left: Consensus distribution (how many runs got 0, 1, 2, 3, 4, 5 approvals)
    ax = axes[1, 0]
    bins = np.arange(-0.5, n_ag + 1.5, 1)
    ax.hist(consensus_scores, bins=bins, color='purple', alpha=0.7, edgecolor='black', align='mid')
    ax.set_xlabel('Number of Agents Approving', fontweight='bold')
    ax.set_ylabel('Number of Runs', fontweight='bold')
    ax.set_title(f'Consensus Distribution (Out of {n_ag} Agents)', fontweight='bold')
    ax.set_xticks(range(n_ag + 1))
    ax.grid(True, alpha=0.3, axis='y')

    # Bottom-right: Budget allocation (F1–F4) per agent – avg when agent target met vs not met
    ax = axes[1, 1]
    f1 = [r.get('F1', 25) for r in runs]
    f2 = [r.get('F2', 25) for r in runs]
    f3 = [r.get('F3', 25) for r in runs]
    f4 = [r.get('F4', 25) for r in runs]
    x = np.arange(n_ag)
    width = 0.35
    # For each agent: avg F1 when met vs not met (two bars per agent)
    met_avg_f1, notmet_avg_f1 = [], []
    met_avg_f2, notmet_avg_f2 = [], []
    met_avg_f3, notmet_avg_f3 = [], []
    met_avg_f4, notmet_avg_f4 = [], []
    for m in meets_list[:n_ag]:
        met_idx = [i for i in range(len(runs)) if m[i]]
        not_idx = [i for i in range(len(runs)) if not m[i]]
        met_avg_f1.append(np.mean([f1[i] for i in met_idx]) if met_idx else 0)
        notmet_avg_f1.append(np.mean([f1[i] for i in not_idx]) if not_idx else 0)
        met_avg_f2.append(np.mean([f2[i] for i in met_idx]) if met_idx else 0)
        notmet_avg_f2.append(np.mean([f2[i] for i in not_idx]) if not_idx else 0)
        met_avg_f3.append(np.mean([f3[i] for i in met_idx]) if met_idx else 0)
        notmet_avg_f3.append(np.mean([f3[i] for i in not_idx]) if not_idx else 0)
        met_avg_f4.append(np.mean([f4[i] for i in met_idx]) if met_idx else 0)
        notmet_avg_f4.append(np.mean([f4[i] for i in not_idx]) if not_idx else 0)
    # Stacked bars: "Target met" (left) vs "Target not met" (right) per agent; each bar = F1+F2+F3+F4
    for i in range(n_ag):
        ax.bar(x[i] - width/2, met_avg_f1[i], width/2, label='F1' if i == 0 else None, color='green', alpha=0.8)
        ax.bar(x[i] - width/2, met_avg_f2[i], width/2, bottom=met_avg_f1[i], label='F2' if i == 0 else None, color='blue', alpha=0.8)
        ax.bar(x[i] - width/2, met_avg_f3[i], width/2, bottom=np.array(met_avg_f1)[i]+np.array(met_avg_f2)[i], label='F3' if i == 0 else None, color='orange', alpha=0.8)
        ax.bar(x[i] - width/2, met_avg_f4[i], width/2, bottom=np.array(met_avg_f1)[i]+np.array(met_avg_f2)[i]+np.array(met_avg_f3)[i], label='F4' if i == 0 else None, color='red', alpha=0.8)
        ax.bar(x[i], notmet_avg_f1[i], width/2, color='green', alpha=0.4)
        ax.bar(x[i], notmet_avg_f2[i], width/2, bottom=notmet_avg_f1[i], color='blue', alpha=0.4)
        ax.bar(x[i], notmet_avg_f3[i], width/2, bottom=np.array(notmet_avg_f1)[i]+np.array(notmet_avg_f2)[i], color='orange', alpha=0.4)
        ax.bar(x[i], notmet_avg_f4[i], width/2, bottom=np.array(notmet_avg_f1)[i]+np.array(notmet_avg_f2)[i]+np.array(notmet_avg_f3)[i], color='red', alpha=0.4)
    ax.set_xticks(x)
    ax.set_xticklabels(agent_list, rotation=25, ha='right')
    ax.set_ylabel('Avg F1–F4 Allocation (%)', fontweight='bold')
    ax.set_title('Budget Allocation by Agent: Target Met (left) vs Not Met (right)', fontweight='bold')
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(facecolor='green', alpha=0.8, label='F1'), Patch(facecolor='blue', alpha=0.8, label='F2'),
                      Patch(facecolor='orange', alpha=0.8, label='F3'), Patch(facecolor='red', alpha=0.8, label='F4')],
             loc='upper right', ncol=2)
    ax.grid(True, alpha=0.3, axis='y')

    plt.tight_layout()
    plt.savefig('outputs/paper_figures/strategy_evaluation_mainagents.png', dpi=300, bbox_inches='tight')
    print("Saved strategy_evaluation_mainagents.png (5 agents)")
    plt.close()


def main():
    """Generate all visualizations."""
    print("=" * 70)
    print("Generating Paper Visualizations")
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
    
    print("\n" + "=" * 70)
    print("All visualizations generated!")
    print("=" * 70)

if __name__ == '__main__':
    main()

