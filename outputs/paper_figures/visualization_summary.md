# Visualization Summary: Multi-Agent Framework for Cyber-Risk Management

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
