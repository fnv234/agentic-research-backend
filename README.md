# Agentic Research Backend

A production-ready Python backend service for multi-agent research systems with seamless React frontend integration. Flask API for agents, simulation runs, thresholds, and analysis.

## Project Structure

```
agentic-research-backend/
├── app/
│   ├── __init__.py
│   ├── agents.py          # Agent definitions (ExecutiveBot, BoardRoom, CFO, CRO, COO, etc.)
│   └── dashboard.py       # Flask API server and all endpoints
├── data/
│   ├── __init__.py
│   ├── data_loader.py     # Data loading (CSV, manual, mock)
│   ├── forio_client.py    # Forio API client
│   ├── forio_data_api.py  # Forio data API
│   └── mongodb_client.py  # MongoDB (thresholds, simulation comparison)
├── scripts/               # Utility scripts (calibration, optimization, visualizations)
├── outputs/               # Analysis outputs and figures
├── tests/                 # API and connection tests
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── wsgi.py                # WSGI entry (Gunicorn/Render)
├── endpoints.md           # Endpoint reference
└── README.md
```

Optional for full functionality:

- `config/agent_config.json` — agent configuration (KPIs, targets, personalities). If missing, agents use defaults.
- `data/sim_data.csv` — real simulation data for runs, compare, and benchmark. If missing, mock data is used.

## Running the API

- **Local**: `python -m app.dashboard` or `flask --app app.dashboard run` (default: `http://0.0.0.0:5001`)
- **Production**: `gunicorn -w 4 -b 0.0.0.0:5001 wsgi:app`
- **Environment**: `HOST`, `PORT` (default 5001), `DEBUG`, `CORS_ORIGINS`

## API Endpoints

### Root & Health

| Method | Endpoint   | Description                          |
|--------|------------|--------------------------------------|
| `GET`  | `/`        | API greeting and service name        |
| `GET`  | `/health`  | Health check (status, timestamp)     |
| `GET`  | `/api/info`| Service info, agent count, data sources (csv/manual/mock) |

### Agents

| Method | Endpoint   | Description                                  |
|--------|------------|----------------------------------------------|
| `GET`  | `/api/bots`| List all agents (name, kpi_focus, target, personality) |

### Data & Runs

| Method | Endpoint            | Description |
|--------|---------------------|-------------|
| `GET`  | `/api/runs`         | Simulated/bot runs (manual or mock). Returns `{ success, count, data }`. |
| `GET`  | `/api/runs/real`    | Real data from CSV. Returns `{ success, count, data }`. |
| `POST` | `/api/evaluate`     | Evaluate a run with agents. Body: `{ "run": { ... } }`. Returns feedback, recommendations, interaction. |
| `GET`  | `/api/runs/compare` | Compare real vs bot data (best/avg by profit, security, availability, detailed_comparison). |
| `GET`  | `/api/statistics`   | Statistical summary (real_data, bot_data, data_sources). |

### Simulation

| Method | Endpoint       | Description |
|--------|----------------|-------------|
| `GET`  | `/api/scenarios` | List simulation scenarios (simple_deterministic, simple_unpredictable, ransomware, ransomware_ransom). |
| `POST` | `/api/simulate`  | Run multi-agent simulation. Body: `scenario`, `agent_collaboration`, `risk_tolerance`, `num_years`. Returns time_series, summary, agent_perspectives. |

### Thresholds (MongoDB)

| Method   | Endpoint                      | Description |
|----------|-------------------------------|-------------|
| `POST`   | `/api/thresholds`             | Create threshold. Body: `agent_name`, `kpi_name`, `min_value`, `max_value`, `target_value`, `description`. |
| `GET`    | `/api/thresholds`             | List thresholds. Query: `?agent=<name>` to filter by agent. |
| `GET`    | `/api/thresholds/<id>`        | Get one threshold. |
| `PUT`    | `/api/thresholds/<id>`        | Update threshold. Body: fields to update. |
| `DELETE` | `/api/thresholds/<id>`        | Delete threshold. |
| `GET`    | `/api/thresholds/<id>/history`| Comparison history for threshold. Query: `?limit=100`. |

### Threshold Statistics & Simulation Logging

| Method | Endpoint                                | Description |
|--------|-----------------------------------------|-------------|
| `GET`  | `/api/statistics/thresholds`            | Threshold compliance stats. Query: `?threshold_id=`, `?agent=`, `?days=30`. |
| `POST` | `/api/simulations/<sim_id>/log`         | Log a simulation run. Body: `threshold_id`, `agent_name`, `kpi_name`, `actual_value`, `target_value`, etc. |
| `GET`  | `/api/simulations/<sim_id>/results`      | Get results for a simulation. |
| `POST` | `/api/simulations/<sim_id>/compare`     | Log comparison result. Body: `threshold_id`, `is_within_threshold`, `actual_value`, `threshold_min`, `threshold_max`, `notes`. |

### Analysis

| Method | Endpoint                         | Description |
|--------|----------------------------------|-------------|
| `GET`  | `/api/analysis/architecture`     | Multi-agent architecture and design (agents, scenarios, key_mechanisms). |
| `POST` | `/api/analysis/strategic-control`| Effect of collaboration. Body: `scenario`, `num_years`. |
| `POST` | `/api/analysis/risk-reward`      | Risk tolerance vs reward. Body: `scenario`. |
| `GET`  | `/api/analysis/benchmark`        | Real data benchmark (from `data/sim_data.csv`). |

## Dependencies

See `requirements.txt`: Flask, Flask-CORS, gunicorn, python-dotenv, requests, pandas, numpy, pymongo, matplotlib; pytest/pytest-cov for tests.
