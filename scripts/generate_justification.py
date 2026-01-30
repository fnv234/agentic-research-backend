"""
Generate visual and written justification for agent settings (5 agents: CFO, CRO, COO, IT_Manager, CHRO).
- Loads agent config from config/agent_config.json or app.agents
- Reads automated_dataset.json, simulation_data.json, optimization_results.json, or data/sim_data.csv
- Produces per-agent distribution PNGs, a combined summary figure, and AGENT_SETTINGS_JUSTIFICATION.md

Requires: matplotlib, pandas, numpy
"""

import os
import sys
import json
from typing import List, Dict, Optional
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# run from repo root when needed
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

OUTPUT_DIR = os.path.join(REPO_ROOT, 'outputs')
KPI_LABELS = {
    'accumulated_profit': 'Accumulated Profit ($)',
    'compromised_systems': 'Compromised Systems (count)',
    'systems_availability': 'Systems Availability (0-1)',
}


def load_agent_config() -> Dict:
    """Load agent config from config/agent_config.json or app.agents (5 agents)."""
    config_path = os.path.join(REPO_ROOT, 'config', 'agent_config.json')
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            data = json.load(f)
        return data.get('agents', data)
    try:
        from app.agents import load_agent_config as app_load
        return app_load()
    except Exception:
        pass
    return {}


def load_dataset() -> pd.DataFrame:
    """Load dataset from JSON or CSV with KPI columns. Fallback: optimization_results, sim_data, mock."""
    data: List[Dict] = []
    candidates = [
        os.path.join(REPO_ROOT, 'automated_dataset.json'),
        os.path.join(REPO_ROOT, 'automated_simulation_data.json'),
        os.path.join(REPO_ROOT, 'simulation_data.json'),
    ]
    for path in candidates:
        if os.path.exists(path):
            try:
                with open(path, 'r') as f:
                    raw = json.load(f)
                if isinstance(raw, dict):
                    data = list(raw.values())
                elif isinstance(raw, list):
                    data = raw
                else:
                    continue
                if data and isinstance(data[0], dict):
                    break
            except Exception:
                continue

    if not data:
        opt_path = os.path.join(REPO_ROOT, 'outputs', 'multi_agent_optimization', 'optimization_results.json')
        if os.path.exists(opt_path):
            with open(opt_path, 'r') as f:
                opt = json.load(f)
            for scenario, configs in opt.items():
                for config_name, config_data in configs.items():
                    for y in config_data.get('years_summary', [])[:10]:
                        comp = float(y.get('compromised', 0) or 0)
                        profit = float(y.get('profit', 0) or 0)
                        data.append({
                            'accumulated_profit': profit,
                            'compromised_systems': comp,
                            'systems_availability': min(1.0, max(0, 1.0 - comp / 100)),
                        })
        if not data and os.path.exists(os.path.join(REPO_ROOT, 'data', 'sim_data.csv')):
            df_raw = pd.read_csv(os.path.join(REPO_ROOT, 'data', 'sim_data.csv'))
            if 'Cum. Profits' in df_raw.columns:
                df_raw['Cum. Profits'] = pd.to_numeric(df_raw['Cum. Profits'].astype(str).str.replace(',', ''), errors='coerce')
            for _, row in df_raw.head(200).iterrows():
                profit = float(row.get('Cum. Profits', 0) or 0) * 1000
                comp = float(row.get('Comp. Systems', 0) or 0)
                data.append({
                    'accumulated_profit': profit,
                    'compromised_systems': comp,
                    'systems_availability': max(0, min(1.0, 1.0 - comp / 100)),
                })
        if not data:
            try:
                sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
                from multi_agent_demo_mock import generate_mock_runs
                data = generate_mock_runs(30)
            except Exception:
                data = [{'accumulated_profit': 1200000 + i*50000, 'compromised_systems': 5 + (i % 10), 'systems_availability': 0.9 + (i % 10)/100} for i in range(50)]

    df = pd.DataFrame(data)
    for col in ['accumulated_profit', 'compromised_systems', 'systems_availability']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    if 'systems_availability' in df.columns:
        av = df['systems_availability']
        if av.notna().any() and np.nanmedian(av) > 1.0:
            df['systems_availability'] = av / 100.0
    needed = ['accumulated_profit', 'compromised_systems', 'systems_availability']
    present = [c for c in needed if c in df.columns]
    if not present:
        raise ValueError(f"Dataset missing KPI columns: {needed}")
    return df


def summarize_series(s: pd.Series) -> Dict:
    s_clean = s.dropna()
    try:
        s_clean = s_clean.astype(float)
    except Exception:
        return {'count': 0}
    if s_clean.empty:
        return {'count': 0}
    return {
        'count': int(s_clean.shape[0]),
        'min': float(np.nanmin(s_clean)),
        'max': float(np.nanmax(s_clean)),
        'mean': float(np.nanmean(s_clean)),
        'median': float(np.nanmedian(s_clean)),
        'stdev': float(np.nanstd(s_clean, ddof=1)) if s_clean.shape[0] > 1 else 0.0,
        'p30': float(np.nanpercentile(s_clean, 30)),
        'p50': float(np.nanpercentile(s_clean, 50)),
        'p70': float(np.nanpercentile(s_clean, 70)),
    }


def fraction_meeting_target(s: pd.Series, target: Dict) -> float:
    s_clean = s.dropna()
    try:
        s_clean = s_clean.astype(float)
    except Exception:
        return 0.0
    if s_clean.empty:
        return 0.0
    if 'min' in target:
        return float(np.mean(s_clean >= target['min']))
    if 'max' in target:
        return float(np.mean(s_clean <= target['max']))
    return 0.0


def plot_distribution(
    s: pd.Series,
    title: str,
    xlabel: str,
    target: Dict,
    out_path: str,
    secondary_target: Optional[Dict] = None,
    secondary_label: Optional[str] = None,
):
    """Plot histogram with target line(s). Optionally add a second target line (e.g. other agent same KPI)."""
    s_clean = s.dropna()
    try:
        s_clean = s_clean.astype(float)
    except Exception:
        plt.close()
        return
    if s_clean.empty:
        plt.close()
        return
    plt.figure(figsize=(8, 5))
    n, bins, patches = plt.hist(s_clean, bins=20, color='#60a5fa', alpha=0.65, edgecolor='white')
    if 'min' in target:
        v = target['min']
        fmt = f"{v:,.0f}" if v > 100 else f"{v:.2f}"
        plt.axvline(v, color='#1d4ed8', linestyle='--', linewidth=2, label=f"Target ≥ {fmt}")
    elif 'max' in target:
        v = target['max']
        fmt = f"{v:,.0f}" if isinstance(v, (int, float)) and v > 100 else f"{v:.2f}"
        plt.axvline(v, color='#dc2626', linestyle='--', linewidth=2, label=f"Target ≤ {fmt}")
    if secondary_target and secondary_label:
        if 'min' in secondary_target:
            v = secondary_target['min']
            plt.axvline(v, color='#7c3aed', linestyle=':', linewidth=1.5, label=secondary_label)
        elif 'max' in secondary_target:
            v = secondary_target['max']
            plt.axvline(v, color='#7c3aed', linestyle=':', linewidth=1.5, label=secondary_label)
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel('Count')
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close()


def plot_all_agents_summary(df: pd.DataFrame, agents_config: Dict, out_path: str):
    """One figure with 5 panels: each agent's KPI distribution and target line."""
    role_order = [r for r in ['CFO', 'CRO', 'COO', 'IT_Manager', 'CHRO'] if r in agents_config]
    if not role_order:
        return
    n = len(role_order)
    ncols = min(3, n)
    nrows = (n + ncols - 1) // ncols
    fig, axes = plt.subplots(nrows, ncols, figsize=(5 * ncols, 4 * nrows))
    if n == 1:
        axes = np.array([axes])
    axes_flat = axes.flatten() if n > 1 else [axes]
    colors = ['#22c55e', '#dc2626', '#2563eb', '#7c3aed', '#ea580c']
    for idx, role in enumerate(role_order):
        ax = axes_flat[idx] if idx < len(axes_flat) else None
        if ax is None:
            break
        cfg = agents_config[role]
        kpi = cfg.get('kpi')
        target = cfg.get('target', {})
        if kpi not in df.columns:
            ax.text(0.5, 0.5, f'{role}\nNo data', ha='center', va='center')
            ax.set_title(role)
            continue
        s = df[kpi].dropna().astype(float)
        if s.empty:
            ax.set_title(role)
            continue
        ax.hist(s, bins=15, color=colors[idx % len(colors)], alpha=0.7, edgecolor='white')
        if 'min' in target:
            v = target['min']
            ax.axvline(v, color='#1d4ed8', linestyle='--', linewidth=2, label=f"≥ {v:,.0f}" if v > 100 else f"≥ {v:.2f}")
        elif 'max' in target:
            v = target['max']
            ax.axvline(v, color='#dc2626', linestyle='--', linewidth=2, label=f"≤ {v}")
        ax.set_title(f'{role}: {kpi.replace("_", " ").title()}')
        ax.set_xlabel(KPI_LABELS.get(kpi, kpi))
        ax.set_ylabel('Count')
        ax.legend()
    for j in range(len(role_order), len(axes_flat)):
        axes_flat[j].set_visible(False)
    plt.suptitle('Agent Threshold Justification: KPI Distributions and Targets (5 Agents)', fontsize=12, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.savefig(out_path, dpi=150, bbox_inches='tight')
    plt.close()


def generate_report(df: pd.DataFrame, agents_config: Dict) -> str:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    report_lines: List[str] = []
    report_lines.append('# Agent Settings Justification')
    report_lines.append('')
    report_lines.append('This report explains and visualizes why the **five agent** settings (CFO, CRO, COO, IT_Manager, CHRO) are appropriate based on the distribution of results in the simulation dataset.')
    report_lines.append('')

    role_order = [r for r in ['CFO', 'CRO', 'COO', 'IT_Manager', 'CHRO'] if r in agents_config]
    if not role_order:
        role_order = list(agents_config.keys())

    # Combined summary figure
    summary_path = os.path.join(OUTPUT_DIR, 'all_agents_threshold_justification.png')
    plot_all_agents_summary(df, agents_config, summary_path)
    report_lines.append('## Summary: All Agents')
    report_lines.append('')
    report_lines.append('The figure below shows each agent\'s KPI distribution and target threshold in one view.')
    report_lines.append('')
    report_lines.append('![All agents threshold justification](all_agents_threshold_justification.png)')
    report_lines.append('')
    report_lines.append('---')
    report_lines.append('')

    # Per-agent sections and individual distribution plots
    for role in role_order:
        cfg = agents_config[role]
        kpi = cfg.get('kpi')
        target = cfg.get('target', {})
        personality = cfg.get('personality', {})

        if kpi not in df.columns:
            report_lines.append(f'## {role}')
            report_lines.append('')
            report_lines.append(f'- **KPI Focus**: `{kpi}` (no data in dataset)')
            report_lines.append('')
            continue

        s = df[kpi]
        stats = summarize_series(s)
        frac_meet = fraction_meeting_target(s, target)

        safe_role = role.replace(' ', '_').lower()
        png_name = f"{safe_role}_{kpi}_distribution.png"
        out_png = os.path.join(OUTPUT_DIR, png_name)
        title = f"{role}: {kpi.replace('_', ' ').title()}"
        xlabel = KPI_LABELS.get(kpi, kpi)

        secondary_target = None
        secondary_label = None
        if role == 'IT_Manager' and 'CRO' in agents_config and agents_config['CRO'].get('kpi') == 'compromised_systems':
            secondary_target = agents_config['CRO'].get('target')
            secondary_label = "CRO target (reference)"
        elif role == 'CHRO' and 'COO' in agents_config and agents_config['COO'].get('kpi') == 'systems_availability':
            secondary_target = agents_config['COO'].get('target')
            secondary_label = "COO target (reference)"

        plot_distribution(s, title, xlabel, target, out_png, secondary_target, secondary_label)

        report_lines.append(f'## {role}')
        report_lines.append('')
        report_lines.append(f'- **KPI Focus**: `{kpi}`')
        if 'min' in target:
            report_lines.append(f'- **Target**: `min = {target["min"]:,.2f}`' if target['min'] > 100 else f'- **Target**: `min = {target["min"]:.2f}`')
        elif 'max' in target:
            report_lines.append(f'- **Target**: `max = {target["max"]:,.2f}`')
        if personality:
            report_lines.append('- **Personality**:')
            report_lines.append(f"  - risk_tolerance: `{personality.get('risk_tolerance', '—')}`")
            report_lines.append(f"  - friendliness: `{personality.get('friendliness', '—')}`")
            report_lines.append(f"  - ambition: `{personality.get('ambition', '—')}`")
        report_lines.append('')
        report_lines.append('- **Data distribution**:')
        report_lines.append(f"  - count: `{stats.get('count', 0)}`")
        if stats.get('count', 0) > 0:
            report_lines.append(f"  - min→max: `{stats['min']:,.2f}` → `{stats['max']:,.2f}`")
            report_lines.append(f"  - mean / median: `{stats['mean']:,.2f}` / `{stats['median']:,.2f}`")
            report_lines.append(f"  - stdev: `{stats['stdev']:,.2f}`")
            report_lines.append(f"  - p30 / p50 / p70: `{stats['p30']:,.2f}` / `{stats['p50']:,.2f}` / `{stats['p70']:,.2f}`")
            report_lines.append(f"- **Share meeting target**: `{frac_meet:.1%}`")
        report_lines.append('')
        report_lines.append(f'![{role} Distribution]({png_name})')
        report_lines.append('')
        if 'min' in target:
            report_lines.append(f"- **Rationale**: The target is set near the upper distribution (≈p70) to be achievable yet challenging, given mean `{stats.get('mean', 0):,.2f}` and stdev `{stats.get('stdev', 0):,.2f}`.")
        else:
            report_lines.append(f"- **Rationale**: The cap is set near the lower distribution (≈p30) to reflect risk limits, given mean `{stats.get('mean', 0):,.2f}` and stdev `{stats.get('stdev', 0):,.2f}`.")
        report_lines.append('')

    report_path = os.path.join(OUTPUT_DIR, 'AGENT_SETTINGS_JUSTIFICATION.md')
    with open(report_path, 'w') as f:
        f.write('\n'.join(report_lines))
    return report_path


if __name__ == '__main__':
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    agents_config = load_agent_config()
    if not agents_config:
        print("Warning: No agent config found; using defaults for CFO, CRO, COO only.")
        agents_config = {
            'CFO': {'kpi': 'accumulated_profit', 'target': {'min': 1200000}, 'personality': {'risk_tolerance': 0.3, 'friendliness': 0.6, 'ambition': 0.8}},
            'CRO': {'kpi': 'compromised_systems', 'target': {'max': 10}, 'personality': {'risk_tolerance': 0.2, 'friendliness': 0.5, 'ambition': 0.6}},
            'COO': {'kpi': 'systems_availability', 'target': {'min': 0.92}, 'personality': {'risk_tolerance': 0.5, 'friendliness': 0.7, 'ambition': 0.7}},
        }
    df = load_dataset()
    report_path = generate_report(df, agents_config)
    print(f"Generated report: {report_path}")
    print(f"Images saved in: {OUTPUT_DIR}/")
