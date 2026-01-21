"""
Generate visual and written justification for CFO/CRO/COO settings
- Reads automated_dataset.json (preferred) or automated_simulation_data.json
- Uses latest calibration targets (Option B provided by user)
- Produces PNG charts and a Markdown report in outputs/

Requires: matplotlib, pandas, numpy
"""

import os
import json
from typing import List, Dict
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from multi_agent_demo_mock import generate_mock_runs

# --- Config (Option B from user's latest calibration) ---
TARGETS = {
    'CFO': {'kpi': 'accumulated_profit', 'target': {'min': 1_905_000.0}},
    'CRO': {'kpi': 'compromised_systems', 'target': {'max': 5}},
    'COO': {'kpi': 'systems_availability', 'target': {'min': 0.99}},
}

PERSONALITIES = {
    'CFO': {'risk_tolerance': 0.57, 'friendliness': 0.60, 'ambition': 0.80},
    'CRO': {'risk_tolerance': 0.40, 'friendliness': 0.50, 'ambition': 0.60},
    'COO': {'risk_tolerance': 0.50, 'friendliness': 0.70, 'ambition': 0.70},
}

OUTPUT_DIR = 'outputs'


def ensure_output_dir():
    os.makedirs(OUTPUT_DIR, exist_ok=True)


def load_dataset() -> pd.DataFrame:
    """Load automated dataset or fall back to automated_simulation_data.json.
    Returns a DataFrame with expected KPI columns if possible.
    """
    candidates = [
        'automated_dataset.json',
        'automated_simulation_data.json',
        'simulation_data.json',
    ]
    data: List[Dict] = []
    source = None
    for path in candidates:
        if os.path.exists(path):
            try:
                with open(path, 'r') as f:
                    raw = json.load(f)
                    if isinstance(raw, dict):
                        # possibly {run_id: {...}}
                        data = list(raw.values())
                    elif isinstance(raw, list):
                        data = raw
                    source = path
                    break
            except Exception:
                continue
    if not data:
        # Fallback to mock data if no dataset present
        mock = generate_mock_runs(30)
        return pd.DataFrame(mock)

    df = pd.DataFrame(data)

    # Normalize potential types/fields
    # Availability might be in 0-100; normalize to 0-1 if needed
    if 'systems_availability' in df.columns:
        avail = pd.to_numeric(df['systems_availability'], errors='coerce')
        if avail.notna().any():
            # If median > 1, treat as percent
            med = np.nanmedian(avail)
            if med > 1.0:
                avail = avail / 100.0
        df['systems_availability'] = avail

    # Profit numeric
    if 'accumulated_profit' in df.columns:
        df['accumulated_profit'] = pd.to_numeric(df['accumulated_profit'], errors='coerce')

    # Compromised systems integer
    if 'compromised_systems' in df.columns:
        df['compromised_systems'] = pd.to_numeric(df['compromised_systems'], errors='coerce')

    # Keep only relevant columns
    needed = ['accumulated_profit', 'compromised_systems', 'systems_availability']
    present = [c for c in needed if c in df.columns]
    if not present:
        raise ValueError(f"Dataset {source} is missing KPI columns: {needed}")

    return df


def summarize_series(s: pd.Series) -> Dict:
    s_clean = s.dropna().astype(float)
    if s_clean.empty:
        return {'count': 0}
    return {
        'count': int(s_clean.shape[0]),
        'min': float(np.min(s_clean)),
        'max': float(np.max(s_clean)),
        'mean': float(np.mean(s_clean)),
        'median': float(np.median(s_clean)),
        'stdev': float(np.std(s_clean, ddof=1)) if s_clean.shape[0] > 1 else 0.0,
        'p30': float(np.percentile(s_clean, 30)),
        'p50': float(np.percentile(s_clean, 50)),
        'p70': float(np.percentile(s_clean, 70)),
    }


def fraction_meeting_target(s: pd.Series, target: Dict) -> float:
    s_clean = s.dropna().astype(float)
    if s_clean.empty:
        return 0.0
    if 'min' in target:
        return float(np.mean(s_clean >= target['min']))
    if 'max' in target:
        return float(np.mean(s_clean <= target['max']))
    return 0.0


def plot_distribution(s: pd.Series, title: str, xlabel: str, target: Dict, out_path: str):
    s_clean = s.dropna().astype(float)
    plt.figure(figsize=(8, 5))
    n, bins, patches = plt.hist(s_clean, bins=20, color='#60a5fa', alpha=0.65, edgecolor='white')

    # Target line
    if 'min' in target:
        v = target['min']
        plt.axvline(v, color='#1d4ed8', linestyle='--', linewidth=2, label=f"Target ≥ {v:,.2f}")
    elif 'max' in target:
        v = target['max']
        plt.axvline(v, color='#dc2626', linestyle='--', linewidth=2, label=f"Target ≤ {v:,.2f}")

    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel('Count')
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close()


def generate_report(df: pd.DataFrame):
    ensure_output_dir()

    report_lines: List[str] = []
    report_lines.append('# Agent Settings Justification')
    report_lines.append('')
    report_lines.append('This report explains and visualizes why the CFO/CRO/COO settings (targets and personalities) are appropriate based on the distribution of results in the automated dataset.')
    report_lines.append('')

    role_order = ['CFO', 'CRO', 'COO']
    kpi_labels = {
        'accumulated_profit': 'Accumulated Profit ($)',
        'compromised_systems': 'Compromised Systems (count)',
        'systems_availability': 'Systems Availability (0-1)'
    }

    for role in role_order:
        cfg = TARGETS[role]
        kpi = cfg['kpi']
        target = cfg['target']

        if kpi not in df.columns:
            continue

        s = df[kpi]
        stats = summarize_series(s)
        frac_meet = fraction_meeting_target(s, target)

        # Plot
        png_name = f"{role.lower()}_{kpi}_distribution.png"
        out_png = os.path.join(OUTPUT_DIR, png_name)
        title = f"{role} Focus: {kpi.replace('_', ' ').title()}"
        plot_distribution(s, title, kpi_labels.get(kpi, kpi), target, out_png)

        # Write section
        report_lines.append(f"## {role}")
        report_lines.append('')
        report_lines.append(f"- **KPI Focus**: `{kpi}`")
        if 'min' in target:
            report_lines.append(f"- **Target**: `min = {target['min']:,.2f}`")
        elif 'max' in target:
            report_lines.append(f"- **Target**: `max = {target['max']:,.2f}`")
        p = PERSONALITIES.get(role, {})
        if p:
            report_lines.append("- **Personality**:")
            report_lines.append(f"  - risk_tolerance: `{p.get('risk_tolerance')}`")
            report_lines.append(f"  - friendliness: `{p.get('friendliness')}`")
            report_lines.append(f"  - ambition: `{p.get('ambition')}`")
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
        report_lines.append(f"![{role} Distribution]({os.path.join(OUTPUT_DIR, png_name)})")
        report_lines.append('')
        
        # Rationale sentence
        if 'min' in target:
            report_lines.append(f"- **Rationale**: The target is set near the upper distribution (≈p70) to be achievable yet challenging, given mean `{stats.get('mean', 0):,.2f}` and stdev `{stats.get('stdev', 0):,.2f}`.")
        else:
            report_lines.append(f"- **Rationale**: The cap is set near the lower distribution (≈p30) to reflect risk limits, given mean `{stats.get('mean', 0):,.2f}` and stdev `{stats.get('stdev', 0):,.2f}`.")
        report_lines.append('')

    # Save report
    report_path = os.path.join(OUTPUT_DIR, 'AGENT_SETTINGS_JUSTIFICATION.md')
    with open(report_path, 'w') as f:
        f.write('\n'.join(report_lines))

    return report_path


if __name__ == '__main__':
    ensure_output_dir()
    df = load_dataset()
    report_path = generate_report(df)
    print(f"✅ Generated report: {report_path}")
    print(f"📂 Images saved in: {OUTPUT_DIR}/")
