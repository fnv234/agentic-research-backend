# Agentic Research Backend

A production-ready Python backend service for multi-agent research systems with seamless React frontend integration.

## Project Structure

```
agentic-research-backend/
├── app/
│   ├── agents.py          # Agent definitions (CFO, CRO, COO)
│   └── dashboard.py       # Flask API server
├── data/
│   ├── data_loader.py     # Data loading utilities
│   ├── forio_client.py    # Forio API client
│   ├── forio_data_api.py  # Forio data API
│   └── sim_data.csv       # Simulation data
├── config/
│   └── agent_config.json  # Agent configuration
├── scripts/               # Utility scripts
├── outputs/               # Analysis outputs
├── Dockerfile             # Docker configuration
├── docker-compose.yml     # Docker Compose config
├── requirements.txt       # Python dependencies
├── .env.example          # Environment variables template
├── DEPLOYMENT.md         # Deployment guide
└── README.md             # This file
```

## API Endpoints

### Health & Information
- `GET /health` - Health check
- `GET /api/info` - Service information

### Agents
- `GET /api/bots` - List all agents

### Data
- `GET /api/runs` - Bot simulation runs
- `GET /api/runs/real` - Real data from CSV
- `POST /api/evaluate` - Evaluate a run with bots
- `GET /api/runs/compare` - Compare real vs bot data
- `GET /api/statistics` - Statistical summary