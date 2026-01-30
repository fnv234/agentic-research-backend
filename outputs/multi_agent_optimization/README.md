# Multi-Agent Optimization Results

This directory contains the results of the comprehensive multi-agent optimization analysis for cyber-risk management.

## Files

- **optimization_results.json**: Complete results data in JSON format
  - Contains metrics for all scenarios and agent configurations
  - Includes year-by-year breakdown for each configuration

- **ARCHITECTURE.md**: Detailed architecture documentation
  - System design
  - Agent framework
  - Optimization process
  - Scenario definitions

## Visualizations

- **primary_results.png**: Profit and systems at risk by scenario and configuration
- **collaborative_comparison.png**: Collaborative vs uncollaborative agents across scenarios
- **risk_tolerance_comparison.png**: Low/medium/high risk tolerance across scenarios
- **year_by_year_evolution.png**: 5-year progression for first scenario (backward compatibility)
- **year_by_year_evolution_simple_deterministic.png**: 5-year evolution (simple deterministic threat)
- **year_by_year_evolution_simple_unpredictable.png**: 5-year evolution (simple unpredictable threat)
- **year_by_year_evolution_advanced_ransomware.png**: 5-year evolution (ransomware, no payment)
- **year_by_year_evolution_advanced_ransomware_paid.png**: 5-year evolution (ransomware with payment)

## Scenarios Analyzed

1. **Simple Threats - Deterministic Attacker**
   - Level 1, No ransomware
   - Predictable attack patterns

2. **Simple Threats - Unpredictable Attacker**
   - Level 1, No ransomware
   - Unpredictable attack patterns (simulated with variance)

3. **Advanced Attacks - Ransomware (No Payment)**
   - Ransomware attacks without payment
   - Higher impact scenarios

4. **Advanced Attacks - Ransomware (With Payment)**
   - Ransomware attacks with ransom payment
   - Financial + operational impact

## Agent Framework

The optimization uses **five agents** (CFO, CRO, COO, IT_Manager, CHRO) with distinct KPIs and targets; see ARCHITECTURE.md for roles and allocation logic.

## Agent Configurations

1. **Collaborative**: High ambition, high friendliness
2. **Uncollaborative**: Low ambition, low friendliness
3. **Low Risk Tolerance**: Conservative risk approach
4. **High Risk Tolerance**: Aggressive risk approach

## Key Metrics

- **Total Profit**: Accumulated profit over 5 years
- **Total Systems at Risk**: Cumulative systems at risk
- **Average Compromised Systems**: Average per year
- **Average Systems Availability**: Average availability percentage

## Usage

To regenerate results:

```bash
python scripts/multi_agent_optimization.py
```

To generate summary report:

```bash
python scripts/generate_optimization_report.py
```

## Publication Notes

These results are suitable for publication and demonstrate:
- Multi-agent optimization effectiveness
- Impact of agent collaboration on outcomes
- Risk tolerance trade-offs
- Scenario-specific optimization strategies

