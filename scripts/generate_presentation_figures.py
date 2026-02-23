"""
Generate presentation figures for the dashboard:
1. Investment strategy: % in prevention, detection, response, recovery over simulation years.
2. Sensitivity analysis: many simulations with one parameter varied, single summary graph.

Run from repo root: python scripts/generate_presentation_figures.py
Outputs: outputs/presentation/investment_strategy.png, sensitivity_analysis.png
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import matplotlib.pyplot as plt
import numpy as np

# Import after path is set
from app.dashboard import load_simulation_for_scenario

os.makedirs("outputs/presentation", exist_ok=True)

# Shared plot style
plt.rcParams["figure.figsize"] = (10, 6)
plt.rcParams["font.size"] = 10


def figure_investment_strategy():
    """One simulation: table/chart of % prevention, detection, response, recovery per year."""
    result = load_simulation_for_scenario(
        scenario="ransomware",
        collaboration="collaborative",
        risk_tolerance=0.5,
        years=5,
    )
    ts = result["time_series"]
    if not ts or "prevention_pct" not in ts[0]:
        print("Warning: no investment allocation in time_series; run backend with latest code.")
        return

    years = [t["year"] for t in ts]
    prevention = [t["prevention_pct"] for t in ts]
    detection = [t["detection_pct"] for t in ts]
    response = [t["response_pct"] for t in ts]
    recovery = [t["recovery_pct"] for t in ts]

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.bar(np.array(years) - 0.3, prevention, width=0.2, label="Prevention %", color="#2ecc71")
    ax.bar(np.array(years) - 0.1, detection, width=0.2, label="Detection %", color="#3498db")
    ax.bar(np.array(years) + 0.1, response, width=0.2, label="Response %", color="#e74c3c")
    ax.bar(np.array(years) + 0.3, recovery, width=0.2, label="Recovery %", color="#9b59b6")
    ax.set_xlabel("Year (decision point)")
    ax.set_ylabel("Investment %")
    ax.set_title("Bot investment strategy over the simulation\n(Prevention, Detection, Response, Recovery)")
    ax.set_xticks(years)
    ax.legend(loc="upper right")
    ax.set_ylim(0, 55)
    fig.tight_layout()
    out = "outputs/presentation/investment_strategy.png"
    fig.savefig(out, dpi=150)
    plt.close()
    print(f"Saved {out}")


def figure_sensitivity():
    """Sensitivity: vary risk_tolerance, run many sims, plot final profit in one graph."""
    steps = [0, 0.25, 0.5, 0.75, 1.0]
    series = []
    for rt in steps:
        result = load_simulation_for_scenario(
            scenario="ransomware",
            collaboration="collaborative",
            risk_tolerance=rt,
            years=5,
        )
        s = result["summary"]
        series.append({
            "x_label": f"{int(rt * 100)}%",
            "final_profit": s["final_profit"],
            "final_risk": s["final_risk"],
            "avg_availability": s["avg_availability"],
        })

    fig, ax = plt.subplots(figsize=(8, 5))
    x = np.arange(len(series))
    labels = [d["x_label"] for d in series]
    profits = [d["final_profit"] / 1e6 for d in series]
    bars = ax.bar(x, profits, color="#4d8cff", edgecolor="#0066ff")
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_xlabel("Risk tolerance")
    ax.set_ylabel("Final profit ($M)")
    ax.set_title("Sensitivity analysis: final profit vs risk tolerance\n(Scenario: ransomware, collaborative, 5 years)")
    fig.tight_layout()
    out = "outputs/presentation/sensitivity_analysis.png"
    fig.savefig(out, dpi=150)
    plt.close()
    print(f"Saved {out}")


if __name__ == "__main__":
    print("Generating presentation figures...")
    figure_investment_strategy()
    figure_sensitivity()
    print("Done. Check outputs/presentation/")
