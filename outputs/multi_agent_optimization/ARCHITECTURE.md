# Multi-Agent Framework Architecture for Cyber-Risk Management

## Overview

This document describes the architecture and design of the multi-agent decision support framework for cyber-risk management. The framework integrates simulation-based optimization with personality-driven agent evaluation to optimize budget allocation strategies over multiple years.

## System Architecture

### 1. Core Components

#### 1.1 Simulation Data Layer
- **Purpose**: Loads and processes real simulation data from CSV files
- **Key Classes**:
  - `SimulationDataLoader`: Handles CSV parsing, cleaning, and scenario filtering
- **Responsibilities**:
  - Data loading and validation
  - Scenario-based filtering (simple/advanced threats, ransomware, payment status)
  - Data normalization and cleaning

#### 1.2 Multi-Agent Framework
- **Purpose**: Implements executive agent decision-making logic
- **Key Classes**:
  - `ExecutiveBot`: Individual executive agent with KPI focus and personality
  - `BoardRoom`: Coordinates multiple agents and generates consensus
- **Responsibilities**:
  - Agent evaluation of simulation results
  - Personality-driven recommendation generation
  - Multi-agent consensus building

#### 1.3 Optimization Engine
- **Purpose**: Optimizes budget allocation (F1-F4) over 5-year horizon
- **Key Classes**:
  - `MultiAgentOptimizer`: Main optimization orchestrator
- **Responsibilities**:
  - Year-by-year optimization using agent recommendations
  - F1-F4 allocation adjustment based on agent feedback
  - 5-year cumulative metric calculation

### 2. Agent Design

#### 2.1 Agent Structure

The framework uses **five executive agents** (CFO, CRO, COO, IT_Manager, CHRO). Each `ExecutiveBot` agent consists of three key components:

1. **KPI Focus**: The specific metric the agent monitors
   - **CFO**: `accumulated_profit` (minimize cost, maximize revenue)
   - **CRO**: `compromised_systems` (minimize risk exposure)
   - **COO**: `systems_availability` (maximize operational continuity)
   - **IT_Manager**: `compromised_systems` (stricter cap than CRO; technical security focus)
   - **CHRO**: `systems_availability` (higher floor than COO; readiness and continuity focus)

2. **Target Threshold**: Acceptable performance boundaries
   - Minimum thresholds (for maximize KPIs: profit, availability)
   - Maximum thresholds (for minimize KPIs: compromised systems)

3. **Personality Traits**: Three-dimensional personality model
   - `risk_tolerance`: 0.0 (conservative) to 1.0 (aggressive)
   - `friendliness`: 0.0 (individual-focused) to 1.0 (collaborative)
   - `ambition`: 0.0 (satisfied with minimum) to 1.0 (optimization-driven)

#### 2.2 Agent Evaluation Process

```
1. Extract KPI value from simulation results
2. Compare against target threshold (min/max)
3. Determine status: below target / on target / above target
4. Generate personality-driven commentary
5. Provide strategic recommendation
```

#### 2.3 Personality Impact on Recommendations

- **Risk Tolerance**:
  - Low (<0.3): Conservative recommendations, gradual changes
  - High (>0.7): Aggressive recommendations, bold actions
  - Medium (0.3-0.7): Balanced approach

- **Friendliness**:
  - Low (<0.5): Individual-focused, critical feedback
  - High (>0.7): Collaborative, team-oriented, satisfied with group performance
  - Medium (0.5-0.7): Professional interaction

- **Ambition**:
  - Low (<0.5): Satisfied with meeting minimum targets
  - High (>0.8): Pushes for optimization even when targets are met
  - Medium (0.5-0.8): Balanced performance drive

### 3. Optimization Process

#### 3.1 5-Year Optimization Workflow

```
Year 1:
  - Start with best-performing historical run or initial strategy
  - Extract F1-F4 allocation from data or use initial values
  - Run simulation and collect results

Years 2-5:
  - Evaluate Year N-1 results using all agents
  - Collect agent recommendations
  - Adjust F1-F4 allocation based on:
    * Agent threshold comparisons
    * Personality-driven recommendations
    * Consensus building
  - Run simulation with optimized allocation
  - Collect results
```

#### 3.2 Allocation Adjustment Logic

The optimizer adjusts F1-F4 based on **all five agents’** feedback (adjustments are cumulative when multiple agents trigger):

- **CFO (Profit below target)**:
  - Increase F1 (prevention) by +2%, F2 (detection) by +1%
  - Decrease F3 (response) by -1.5%, F4 (recovery) by -1.5%

- **CRO / IT_Manager (Compromised systems above target)**:
  - Both use the same KPI with different caps (CRO max 10, IT_Manager max 8).
  - When either agent’s target is exceeded: Increase F1 by +3%, F2 by +2%; Decrease F3 by -2%, F4 by -3%.

- **COO / CHRO (Availability below target)**:
  - Both use the same KPI with different floors (COO min 0.92, CHRO min 0.93).
  - When either agent’s target is missed: Increase F1 by +1.5%, F2 by +1%; Decrease F3 by -1%, F4 by -1.5%.

#### 3.3 Constraints

- F1, F2, F3, F4 must sum to 100%
- Individual constraints:
  - F1: 10% ≤ F1 ≤ 60%
  - F2: 10% ≤ F2 ≤ 60%
  - F3: 5% ≤ F3 ≤ 50%
  - F4: 5% ≤ F4 ≤ 50%

### 4. Scenario Definitions

#### 4.1 Threat Scenarios

1. **Simple Threats - Deterministic Attacker**
   - Level = 1, Ransomware = 0, Pay Ransom = 0
   - Predictable attack patterns
   - Lower variance in outcomes

2. **Simple Threats - Unpredictable Attacker**
   - Level = 1, Ransomware = 0, Pay Ransom = 0
   - Unpredictable attack patterns
   - Higher variance in outcomes (simulated with noise)

3. **Advanced Attacks - Ransomware (No Payment)**
   - Level = 1 or 2, Ransomware = 1, Pay Ransom = 0
   - Ransomware attacks without payment
   - Higher impact on systems and business

4. **Advanced Attacks - Ransomware (With Payment)**
   - Level = 1 or 2, Ransomware = 1, Pay Ransom = 1
   - Ransomware attacks with ransom payment
   - Financial impact from payment + operational disruption

#### 4.2 Agent Configuration Variations

1. **Collaborative Configuration**
   - High ambition (+0.2)
   - High friendliness (+0.2)
   - Agents work together, seek consensus

2. **Uncollaborative Configuration**
   - Low ambition (-0.2)
   - Low friendliness (-0.2)
   - Agents focus on individual objectives

3. **Low Risk Tolerance**
   - Risk tolerance reduced by -0.3
   - Conservative recommendations
   - Prioritize security over profit

4. **High Risk Tolerance**
   - Risk tolerance increased by +0.3
   - Aggressive recommendations
   - Willing to take risks for higher returns

### 5. Data Flow

```
CSV Data (sim_data.csv)
    ↓
SimulationDataLoader
    ↓ (filter by scenario)
Scenario Data
    ↓
MultiAgentOptimizer
    ↓ (Year 1)
Initial Strategy
    ↓
Simulation Results (Year 1)
    ↓
Agent Evaluation
    ↓
Recommendations
    ↓
F1-F4 Adjustment
    ↓ (Years 2-5)
Optimized Strategy
    ↓
5-Year Results
    ↓
Metrics Calculation
    ↓
Visualization & Analysis
```

### 6. Key Metrics

#### 6.1 Primary Metrics (for Publication)

- **Accumulated Profit**: Total profit over 5 years
- **Systems at Risk**: Total and average systems at risk over 5 years

#### 6.2 Secondary Metrics

- **Total Compromised Systems**: Cumulative compromised systems
- **Average Compromised Systems**: Average per year
- **Average Systems Availability**: Average availability percentage
- **Final Year Metrics**: Year 5 specific values

### 7. Output Structure

#### 7.1 Results JSON

See json files.

#### 7.2 Visualizations

1. **Primary Results**: Profit and systems at risk by scenario and configuration
2. **Collaborative Comparison**: Collaborative vs uncollaborative across scenarios
3. **Risk Tolerance Comparison**: Low/medium/high risk tolerance across scenarios
4. **Year-by-Year Evolution**: 5-year progression for example scenario

### 8. Design Decisions

#### 8.1 Why Multi-Agent?

- Captures diverse stakeholder perspectives (five agents: CFO, CRO, COO, IT_Manager, CHRO)
- Enables trade-off analysis between competing objectives (profit, risk, continuity)
- Provides realistic decision-making simulation aligned with board-level cyber risk governance

#### 8.2 Why Personality-Driven?

- Adds realism to agent behavior
- Captures human decision-making nuances
- Enables study of collaboration vs competition

#### 8.3 Why 5-Year Horizon?

- Allows observation of long-term strategy evolution
- Captures cumulative effects of decisions
- Aligns with typical business planning cycles

### 9. Limitations and Future Work

#### 9.1 Current Limitations

- F1-F4 allocation is estimated from outcomes (not direct inputs)
- Unpredictability is simulated with noise (not inherent in data)
- Single optimization run per configuration (no statistical analysis)

#### 9.2 Future Enhancements

- Direct F1-F4 input data from simulations
- Statistical analysis across multiple runs
- Machine learning for threshold optimization
- Real-time simulation integration
- Extended time horizons (10+ years)

### 10. References

- Agent framework: `app/agents.py`
- Agent configuration: `config/agent_config.json`
- Simulation data: `data/sim_data.csv`
- Main optimization script: `scripts/multi_agent_optimization.py`

