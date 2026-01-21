# Agent Settings Justification

This report explains and visualizes why the CFO/CRO/COO settings (targets and personalities) are appropriate based on the distribution of results in the automated dataset.

## CFO

- **KPI Focus**: `accumulated_profit`
- **Target**: `min = 1,905,000.00`
- **Personality**:
  - risk_tolerance: `0.57`
  - friendliness: `0.6`
  - ambition: `0.8`

- **Data distribution**:
  - count: `30`
  - min→max: `1,383,495.00` → `2,232,505.00`
  - mean / median: `1,771,762.77` / `1,794,221.00`
  - stdev: `179,228.50`
  - p30 / p50 / p70: `1,722,096.90` / `1,794,221.00` / `1,864,897.60`
- **Share meeting target**: `20.0%`

![CFO Distribution](outputs/cfo_accumulated_profit_distribution.png)

- **Rationale**: The target is set near the upper distribution (≈p70) to be achievable yet challenging, given mean `1,771,762.77` and stdev `179,228.50`.

## CRO

- **KPI Focus**: `compromised_systems`
- **Target**: `max = 5.00`
- **Personality**:
  - risk_tolerance: `0.4`
  - friendliness: `0.5`
  - ambition: `0.6`

- **Data distribution**:
  - count: `30`
  - min→max: `2.00` → `12.00`
  - mean / median: `7.17` / `7.00`
  - stdev: `3.13`
  - p30 / p50 / p70: `5.00` / `7.00` / `9.00`
- **Share meeting target**: `33.3%`

![CRO Distribution](outputs/cro_compromised_systems_distribution.png)

- **Rationale**: The cap is set near the lower distribution (≈p30) to reflect risk limits, given mean `7.17` and stdev `3.13`.

## COO

- **KPI Focus**: `systems_availability`
- **Target**: `min = 0.99`
- **Personality**:
  - risk_tolerance: `0.5`
  - friendliness: `0.7`
  - ambition: `0.7`

- **Data distribution**:
  - count: `30`
  - min→max: `0.93` → `1.00`
  - mean / median: `0.98` / `1.00`
  - stdev: `0.02`
  - p30 / p50 / p70: `0.97` / `1.00` / `1.00`
- **Share meeting target**: `53.3%`

![COO Distribution](outputs/coo_systems_availability_distribution.png)

- **Rationale**: The target is set near the upper distribution (≈p70) to be achievable yet challenging, given mean `0.98` and stdev `0.02`.
