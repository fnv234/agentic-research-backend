"""
Multi-Agent Demo with MOCK DATA
Since the Vensim model doesn't save variables to the database,
this demo uses mock data to show how the system would work.
"""

import matplotlib.pyplot as plt
import random

class ExecutiveBot:
    """Board-level executive agent focusing on a KPI."""
    def __init__(self, name, kpi_focus, target=None, personality=None):
        self.name = name
        self.kpi_focus = kpi_focus
        self.target = target or {}
        self.personality = personality or {
            "risk_tolerance": 0.5,
            "friendliness": 0.5,
            "ambition": 0.5
        }
    
    def evaluate(self, results):
        """Judge simulation outputs according to role focus and personality."""
        kpi_value = results.get(self.kpi_focus)
        
        if kpi_value is None:
            return f"{self.name}: KPI {self.kpi_focus} not found in results"
        
        status = "on target"
        if self.target:
            if kpi_value < self.target.get("min", float("-inf")):
                status = "below target"
            elif kpi_value > self.target.get("max", float("inf")):
                status = "above target"
        
        # Personality-driven commentary
        comment = ""
        if self.personality["risk_tolerance"] > 0.7 and status == "below target":
            comment = "(willing to take risks to improve)"
        elif self.personality["risk_tolerance"] < 0.3 and status == "above target":
            comment = "(concerned about sustainability)"
        elif self.personality["ambition"] > 0.8:
            comment = "(pushing for higher targets)"
        
        return f"{self.name} sees {self.kpi_focus}={kpi_value:,.0f}, status={status} {comment}"


class BoardRoom:
    """Simulates a meeting of bots discussing simulation results."""
    def __init__(self, bots):
        self.bots = bots
    
    def run_meeting(self, results):
        """Let all bots evaluate the simulation run."""
        return [bot.evaluate(results) for bot in self.bots]
    
    def simulate_interaction(self, setting="collaborative"):
        """Simplified placeholder for bot dynamics."""
        if setting == "collaborative":
            return "Bots align toward compromise and shared strategy."
        elif setting == "hostile":
            return "Bots argue over priorities, no consensus reached."
        else:
            return "Neutral interaction, each bot focuses on own KPIs."
    
    def negotiate_strategy(self, current_results):
        """Simulate bots negotiating next strategy based on personalities."""
        recommendations = []
        for bot in self.bots:
            kpi_val = current_results.get(bot.kpi_focus, 0)
            target_min = bot.target.get("min", 0)
            target_max = bot.target.get("max", float("inf"))
            
            if kpi_val < target_min:
                if bot.personality["risk_tolerance"] > 0.6:
                    recommendations.append(f"{bot.name}: Increase investment aggressively")
                else:
                    recommendations.append(f"{bot.name}: Gradual increase recommended")
            elif kpi_val > target_max:
                recommendations.append(f"{bot.name}: Reduce spending, optimize efficiency")
            else:
                recommendations.append(f"{bot.name}: Maintain current strategy")
        
        return recommendations


def generate_mock_runs(n=5):
    """Generate mock simulation data for demonstration."""
    runs = []
    for i in range(n):
        # Simulate different strategies
        prevention = random.randint(30, 70)
        detection = random.randint(20, 50)
        response = random.randint(10, 30)
        
        # Simulate outcomes based on strategy
        profit = 1000000 + (prevention * 15000) + random.randint(-200000, 200000)
        compromised = max(0, 20 - (prevention // 5) - (detection // 10) + random.randint(-3, 3))
        availability = min(1.0, 0.85 + (prevention * 0.002) + (detection * 0.001) + random.uniform(-0.05, 0.05))
        
        runs.append({
            "id": f"mock_run_{i+1}",
            "strategy": f"Strategy {chr(65+i)}",  # A, B, C, etc.
            "prevention_budget": prevention,
            "detection_budget": detection,
            "response_budget": response,
            "accumulated_profit": profit,
            "compromised_systems": compromised,
            "systems_availability": availability
        })
    
    return runs


def plot_kpis_comparison(runs_data, kpis, labels=None):
    """Plot KPIs across multiple runs for comparison."""
    if not runs_data:
        print("No data to plot")
        return
    
    if labels is None:
        labels = [run.get("strategy", f"Run {i+1}") for i, run in enumerate(runs_data)]
    
    fig, axes = plt.subplots(1, len(kpis), figsize=(5*len(kpis), 4))
    if len(kpis) == 1:
        axes = [axes]
    
    for idx, kpi in enumerate(kpis):
        vals = [run.get(kpi, 0) for run in runs_data]
        
        colors = ['steelblue' if v == max(vals) else 'lightsteelblue' for v in vals]
        axes[idx].bar(range(len(labels)), vals, color=colors)
        axes[idx].set_xticks(range(len(labels)))
        axes[idx].set_xticklabels(labels, rotation=45, ha='right')
        axes[idx].set_title(kpi.replace('_', ' ').title())
        axes[idx].set_ylabel('Value')
        axes[idx].grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('kpi_comparison_mock.png', dpi=150, bbox_inches='tight')
    print("📊 Plot saved to kpi_comparison_mock.png")
    plt.show()


def plot_strategy_comparison(runs_data):
    """Plot budget allocation vs outcomes."""
    fig, axes = plt.subplots(1, 2, figsize=(12, 4))
    
    # Budget allocation
    labels = [run.get("strategy", f"Run {i+1}") for i, run in enumerate(runs_data)]
    prevention = [run.get("prevention_budget", 0) for run in runs_data]
    detection = [run.get("detection_budget", 0) for run in runs_data]
    response = [run.get("response_budget", 0) for run in runs_data]
    
    x = range(len(labels))
    width = 0.25
    
    axes[0].bar([i - width for i in x], prevention, width, label='Prevention', color='green', alpha=0.7)
    axes[0].bar(x, detection, width, label='Detection', color='orange', alpha=0.7)
    axes[0].bar([i + width for i in x], response, width, label='Response', color='red', alpha=0.7)
    axes[0].set_xticks(x)
    axes[0].set_xticklabels(labels, rotation=45, ha='right')
    axes[0].set_ylabel('Budget Allocation')
    axes[0].set_title('Budget Strategy')
    axes[0].legend()
    axes[0].grid(axis='y', alpha=0.3)
    
    # Outcomes
    profit = [run.get("accumulated_profit", 0) / 1000000 for run in runs_data]  # In millions
    compromised = [run.get("compromised_systems", 0) for run in runs_data]
    
    ax2 = axes[1]
    ax2.scatter(compromised, profit, s=200, alpha=0.6, c=range(len(runs_data)), cmap='viridis')
    for i, label in enumerate(labels):
        ax2.annotate(label, (compromised[i], profit[i]), fontsize=9, ha='center')
    ax2.set_xlabel('Compromised Systems')
    ax2.set_ylabel('Profit (Millions $)')
    ax2.set_title('Risk vs. Reward')
    ax2.grid(alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('strategy_comparison_mock.png', dpi=150, bbox_inches='tight')
    print("📊 Plot saved to strategy_comparison_mock.png")
    plt.show()


# === Demo Workflow ===
if __name__ == "__main__":
    print("🤖 Multi-Agent Simulation Analysis Demo (MOCK DATA)\n")
    print("=" * 70)
    print("NOTE: Using mock data because the Vensim model doesn't save variables.")
    print("See README.md for instructions on configuring variable saving.")
    print("=" * 70)
    
    # Generate mock simulation runs
    print("\n📊 Generating 5 mock simulation runs with different strategies...")
    runs = generate_mock_runs(5)
    
    # Create executive bots with different personalities
    print("\n🤖 Creating executive bots with distinct personalities...")
    
    cfo = ExecutiveBot(
        "CFO (Conservative)", 
        "accumulated_profit", 
        target={"min": 1200000},
        personality={"risk_tolerance": 0.3, "friendliness": 0.6, "ambition": 0.8}
    )
    
    cro = ExecutiveBot(
        "CRO (Risk-Averse)", 
        "compromised_systems", 
        target={"max": 10},
        personality={"risk_tolerance": 0.2, "friendliness": 0.5, "ambition": 0.6}
    )
    
    coo = ExecutiveBot(
        "COO (Balanced)", 
        "systems_availability", 
        target={"min": 0.92},
        personality={"risk_tolerance": 0.5, "friendliness": 0.7, "ambition": 0.7}
    )
    
    board = BoardRoom([cfo, cro, coo])
    
    # Analyze each run
    print("\n" + "=" * 70)
    print("📊 BOARD MEETING: Analyzing Simulation Results")
    print("=" * 70)
    
    for i, run in enumerate(runs):
        print(f"\n{'─' * 70}")
        print(f"Strategy {run['strategy']}: Prevention={run['prevention_budget']}, "
              f"Detection={run['detection_budget']}, Response={run['response_budget']}")
        print(f"{'─' * 70}")
        
        feedback = board.run_meeting(run)
        for comment in feedback:
            print(f"  • {comment}")
        
        # Get strategy recommendations
        recommendations = board.negotiate_strategy(run)
        print(f"\n  💡 Recommendations:")
        for rec in recommendations:
            print(f"     - {rec}")
    
    # Overall board interaction
    print(f"\n{'=' * 70}")
    print(f"🧠 Board Dynamics: {board.simulate_interaction('collaborative')}")
    print(f"{'=' * 70}")
    
    # Find best strategy
    best_profit = max(runs, key=lambda r: r['accumulated_profit'])
    best_security = min(runs, key=lambda r: r['compromised_systems'])
    best_availability = max(runs, key=lambda r: r['systems_availability'])
    
    print(f"\n📈 Performance Summary:")
    print(f"  • Highest Profit: {best_profit['strategy']} (${best_profit['accumulated_profit']:,.0f})")
    print(f"  • Best Security: {best_security['strategy']} ({best_security['compromised_systems']} compromised)")
    print(f"  • Best Availability: {best_availability['strategy']} ({best_availability['systems_availability']:.1%})")
    
    # Generate plots
    print(f"\n{'=' * 70}")
    print("📈 Generating comparison plots...")
    print(f"{'=' * 70}")
    
    kpis = ["accumulated_profit", "compromised_systems", "systems_availability"]
    plot_kpis_comparison(runs, kpis)
    plot_strategy_comparison(runs)
    
    print("\n✅ Analysis complete!")
    print("\nTo use with real data:")
    print("  1. Configure the Vensim model to save variables (see README.md)")
    print("  2. Run simulations through the Forio web interface")
    print("  3. Use multi_agent_demo.py to analyze real runs")
