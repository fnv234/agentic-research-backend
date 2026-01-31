# API Endpoints

## Root & Health
- `GET /` - API greeting
- `GET /health` - Health check
- `GET /api/info` - Service information and data sources

## Agents
- `GET /api/bots` - List agents (name, kpi_focus, target, personality)

## Data & Runs
- `GET /api/runs` - Get bot/simulated runs
- `GET /api/runs/real` - Get real data (CSV)
- `POST /api/evaluate` - Evaluate a run with agents
- `GET /api/runs/compare` - Compare real vs bot data
- `GET /api/statistics` - Statistical summary

## Simulation
- `GET /api/scenarios` - List simulation scenarios
- `POST /api/simulate` - Run multi-agent simulation

## Thresholds (MongoDB)
- `POST /api/thresholds` - Create threshold
- `GET /api/thresholds` - List thresholds (?agent= optional)
- `GET /api/thresholds/<id>` - Get threshold
- `PUT /api/thresholds/<id>` - Update threshold
- `DELETE /api/thresholds/<id>` - Delete threshold
- `GET /api/thresholds/<id>/history` - Comparison history (?limit= optional)

## Threshold Stats & Simulation Logging
- `GET /api/statistics/thresholds` - Threshold compliance stats (?threshold_id=, ?agent=, ?days=)
- `POST /api/simulations/<sim_id>/log` - Log simulation run
- `GET /api/simulations/<sim_id>/results` - Get simulation results
- `POST /api/simulations/<sim_id>/compare` - Log comparison result

## Analysis
- `GET /api/analysis/architecture` - Architecture and design
- `POST /api/analysis/strategic-control` - Collaboration analysis
- `POST /api/analysis/risk-reward` - Risk-reward analysis
- `GET /api/analysis/benchmark` - Real data benchmark
