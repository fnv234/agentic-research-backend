"""
Evaluate the integrated framework with empirical metrics and figures.
- Loads automated_dataset.json if present, else falls back to automated_simulation_data.json,
  else uses mock runs from multi_agent_demo_mock.generate_mock_runs.
- Initializes CFO/CRO/COO agents and computes:
  - Execution time per evaluation batch (proxy for per-scenario speed)
  - Inter-agent agreement (Fleiss' kappa) over recommendation categories
  - Recommendation distribution and strategic patterns
- Produces figures in outputs/ and a concise markdown summary.

Requires: numpy, pandas, matplotlib
"""

import os
import time
import json
from typing import List, Dict
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from multi_agent_demo_mock import ExecutiveBot, BoardRoom, generate_mock_runs

OUTPUT_DIR = "outputs"

# Default agent definitions (align with paper + earlier config)
CFO = ExecutiveBot(
    "CFO",
    "accumulated_profit",
    target={"min": 1_905_000.0},
    personality={"risk_tolerance": 0.57, "friendliness": 0.60, "ambition": 0.80},
)
CRO = ExecutiveBot(
    "CRO",
    "compromised_systems",
    target={"max": 5},
    personality={"risk_tolerance": 0.40, "friendliness": 0.50, "ambition": 0.60},
)
COO = ExecutiveBot(
    "COO",
    "systems_availability",
    target={"min": 0.99},
    personality={"risk_tolerance": 0.50, "friendliness": 0.70, "ambition": 0.70},
)

BOARD = BoardRoom([CFO, CRO, COO])


def ensure_output_dir():
    os.makedirs(OUTPUT_DIR, exist_ok=True)


def load_dataset() -> pd.DataFrame:
    candidates = [
        "automated_dataset.json",
        "automated_simulation_data.json",
        "simulation_data.json",
    ]
    for path in candidates:
        if os.path.exists(path):
            try:
                with open(path, "r") as f:
                    raw = json.load(f)
                if isinstance(raw, dict):
                    data = list(raw.values())
                else:
                    data = raw
                df = pd.DataFrame(data)
                break
            except Exception:
                continue
    else:
        # Fallback to mock
        data = generate_mock_runs(50)
        df = pd.DataFrame(data)

    # Normalize types
    if "accumulated_profit" in df.columns:
        df["accumulated_profit"] = pd.to_numeric(df["accumulated_profit"], errors="coerce")
    if "compromised_systems" in df.columns:
        df["compromised_systems"] = pd.to_numeric(df["compromised_systems"], errors="coerce")
    if "systems_availability" in df.columns:
        avail = pd.to_numeric(df["systems_availability"], errors="coerce")
        if avail.notna().any() and np.nanmedian(avail) > 1:
            avail = avail / 100.0
        df["systems_availability"] = avail
    return df


def classify_recommendation(bot: ExecutiveBot, run: Dict) -> str:
    """Map bot state to a coarse recommendation label for agreement analysis."""
    kpi_val = run.get(bot.kpi_focus)
    tmin = bot.target.get("min", -np.inf)
    tmax = bot.target.get("max", np.inf)
    if kpi_val is None:
        return "unknown"
    if kpi_val < tmin:
        return "increase"
    if kpi_val > tmax:
        return "decrease"
    return "maintain"


def fleiss_kappa(matrix: np.ndarray) -> float:
    """Compute Fleiss' kappa for multiple raters and categories.
    matrix: N x k where N items, k categories, entries are counts of raters per category.
    """
    N, k = matrix.shape
    n = np.sum(matrix[0])  # raters per item (assumed constant)
    p = np.sum(matrix, axis=0) / (N * n)
    P = (np.sum(matrix * matrix, axis=1) - n) / (n * (n - 1))
    P_bar = np.mean(P)
    P_e = np.sum(p * p)
    if np.isclose(1 - P_e, 0):
        return 0.0
    return float((P_bar - P_e) / (1 - P_e))


def evaluate_and_figure(df: pd.DataFrame):
    ensure_output_dir()

    # Speed metric (proxy): time to evaluate all runs by 3 agents
    start = time.time()
    labels = []  # per-run, per-agent recommendation labels
    for _, row in df.iterrows():
        run = row.to_dict()
        run_labels = [
            classify_recommendation(CFO, run),
            classify_recommendation(CRO, run),
            classify_recommendation(COO, run),
        ]
        labels.append(run_labels)
    elapsed = time.time() - start
    avg_ms_per_run = (elapsed / max(len(df), 1)) * 1000

    # Agreement (Fleiss' kappa)
    cats = ["increase", "maintain", "decrease"]
    mat = []
    for lab3 in labels:
        counts = [lab3.count(c) for c in cats]
        mat.append(counts)
    M = np.array(mat, dtype=float) if mat else np.zeros((0, 3))
    kappa = fleiss_kappa(M) if len(M) else 0.0

    # Recommendation distribution per agent
    dist = {"CFO": {}, "CRO": {}, "COO": {}}
    for agent, name in zip([CFO, CRO, COO], ["CFO", "CRO", "COO"]):
        counts = {c: 0 for c in cats}
        for _, row in df.iterrows():
            lab = classify_recommendation(agent, row.to_dict())
            if lab in counts:
                counts[lab] += 1
        dist[name] = counts

    # Figures
    # 1) KPI histograms
    fig, axes = plt.subplots(1, 3, figsize=(14, 4))
    if "accumulated_profit" in df.columns:
        axes[0].hist(df["accumulated_profit"].dropna(), bins=20, color="#60a5fa", alpha=0.7)
        axes[0].axvline(CFO.target["min"], color="#1d4ed8", linestyle="--", label="Target")
        axes[0].set_title("Profit Distribution")
        axes[0].legend()
    if "compromised_systems" in df.columns:
        axes[1].hist(df["compromised_systems"].dropna(), bins=20, color="#f59e0b", alpha=0.7)
        axes[1].axvline(CRO.target["max"], color="#b91c1c", linestyle="--", label="Cap")
        axes[1].set_title("Compromised Systems")
        axes[1].legend()
    if "systems_availability" in df.columns:
        axes[2].hist(df["systems_availability"].dropna(), bins=20, color="#10b981", alpha=0.7)
        axes[2].axvline(COO.target["min"], color="#065f46", linestyle="--", label="SLO")
        axes[2].set_title("Availability")
        axes[2].legend()
    plt.tight_layout()
    hist_path = os.path.join(OUTPUT_DIR, "kpi_histograms.png")
    plt.savefig(hist_path, dpi=150)
    plt.close()

    # 2) Recommendation distribution bar chart
    fig, ax = plt.subplots(figsize=(6, 4))
    idx = np.arange(3)
    width = 0.25
    cfo_counts = [dist["CFO"].get(c, 0) for c in cats]
    cro_counts = [dist["CRO"].get(c, 0) for c in cats]
    coo_counts = [dist["COO"].get(c, 0) for c in cats]
    ax.bar(idx - width, cfo_counts, width, label="CFO")
    ax.bar(idx, cro_counts, width, label="CRO")
    ax.bar(idx + width, coo_counts, width, label="COO")
    ax.set_xticks(idx)
    ax.set_xticklabels(cats)
    ax.set_ylabel("Count")
    ax.set_title("Agent Recommendation Distribution")
    ax.legend()
    rec_path = os.path.join(OUTPUT_DIR, "recommendation_distribution.png")
    plt.tight_layout()
    plt.savefig(rec_path, dpi=150)
    plt.close()

    # 3) Risk-reward scatter: Profit vs. Compromised (if available)
    if "accumulated_profit" in df.columns and "compromised_systems" in df.columns:
        plt.figure(figsize=(5, 4))
        x = df["accumulated_profit"].astype(float)
        y = df["compromised_systems"].astype(float)
        plt.scatter(x, y, alpha=0.6, s=20, c="#6366f1")
        plt.axvline(CFO.target["min"], color="#1d4ed8", linestyle="--")
        plt.axhline(CRO.target["max"], color="#b91c1c", linestyle="--")
        plt.xlabel("Profit ($)")
        plt.ylabel("Compromised Systems")
        plt.title("Risk-Reward Tradeoff")
        rr_path = os.path.join(OUTPUT_DIR, "risk_reward_scatter.png")
        plt.tight_layout()
        plt.savefig(rr_path, dpi=150)
        plt.close()
    else:
        rr_path = None

    # Markdown summary
    md = [
        "# Framework Evaluation Summary",
        "",
        f"- Runs evaluated: {len(df)}",
        f"- Avg eval time per run: {avg_ms_per_run:.2f} ms",
        f"- Fleiss' kappa (3 agents, 3 categories): {kappa:.2f}",
        "",
        "## Figures",
        f"- KPI histograms: {hist_path}",
        f"- Recommendation distribution: {rec_path}",
    ]
    if rr_path:
        md.append(f"- Risk-reward scatter: {rr_path}")

    with open(os.path.join(OUTPUT_DIR, "EVAL_SUMMARY.md"), "w") as f:
        f.write("\n".join(md))

    print("✅ Evaluation complete")
    print(f"Runs: {len(df)} | Avg eval (ms/run): {avg_ms_per_run:.2f} | Kappa: {kappa:.2f}")
    print("Figures saved in outputs/")


if __name__ == "__main__":
    df = load_dataset()
    evaluate_and_figure(df)
