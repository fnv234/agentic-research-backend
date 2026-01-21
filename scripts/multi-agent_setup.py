"""
Forio Simulation Interface:
  - ForioClient: handles API authentication and simulation data exchange
  - ExecutiveBot: represents a role with KPI-driven evaluation
  - BoardRoom: simulates decision-making among bots

NOTE: This file attempts to CREATE new simulation runs via the Forio Model Run API.
However, the cyberriskmanagement-ransomeware-2023 project is a FACILITATOR-BASED
project, which does not support programmatic run creation via API.

For a working demo that FETCHES and ANALYZES existing runs, use:
    python multi_agent_demo.py

To create runs, use the web interface:
    https://forio.com/app/mitcams/cyberriskmanagement-ransomeware-2023/
    Login as: MIT@2025002 (participant) or MIT@2025001 (facilitator)
"""

import os
import time
import base64
import requests
from dotenv import load_dotenv
import matplotlib.pyplot as plt

# Load API keys from .env file
load_dotenv()
PUBLIC_KEY = os.getenv("PUBLIC_KEY")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
FORIO_ORG = os.getenv("FORIO_ORG", "mitcams")
FORIO_PROJECT = os.getenv("FORIO_PROJECT", "cyberriskmanagement-ransomeware-2023")
FORIO_MODEL = os.getenv("FORIO_MODEL", "model.jl")

if not PUBLIC_KEY or not PRIVATE_KEY:
    raise EnvironmentError("Missing PUBLIC_KEY or PRIVATE_KEY in .env file.")


class ForioClient:
    """
    Handles interaction with the Forio cyber-risk simulation API using PUBLIC_KEY / PRIVATE_KEY.
    - run_simulation: submit decision parameters and start a run
    - get_results: fetch output KPIs for analysis
    """

    def __init__(self, org, project, model, public_key, private_key):
        self.org = org
        self.project = project
        self.model = model
        self.base_url = "https://api.forio.com/v2"
        self.session = requests.Session()
        token = self._get_oauth_token(public_key, private_key)
        self.session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {token}"
        })

    def _get_oauth_token(self, public_key, private_key):
        creds = base64.b64encode(f"{public_key}:{private_key}".encode()).decode()
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Basic {creds}"
        }
        data = {"grant_type": "client_credentials"}
        r = requests.post(f"{self.base_url}/oauth/token", headers=headers, data=data)
        if r.status_code >= 400:
            raise RuntimeError(f"❌ OAuth error {r.status_code}: {r.text}")
        token = r.json().get("access_token")
        if not token:
            raise RuntimeError(f"❌ Missing access_token in OAuth response: {r.text}")
        return token

    def run_simulation(self, params):
        """Run one simulation with given decision params."""
        url = f"{self.base_url}/model/run/"
        body = {
            "account": self.org,
            "project": self.project,
            "model": self.model,
            **params
        }
        response = self.session.post(url, json=body)
        print(f"🔗 POST {url}")
        print(f"Status: {response.status_code}")
        print(f"Response text: {response.text[:300]}")
        if not response.text.strip():
            raise RuntimeError("❌ Empty response from Forio API — check URL or auth keys.")
        if response.status_code >= 400:
            raise RuntimeError(f"❌ API error {response.status_code}: {response.text}")
        try:
            run_info = response.json()
        except Exception as e:
            raise RuntimeError(f"❌ Failed to parse JSON (API returned non-JSON): {response.text[:200]}") from e
        run_id = run_info.get("id") or run_info.get("_id")
        if not run_id:
            raise RuntimeError(f"❌ Missing run ID in response: {run_info}")
        print(f"✅ Started simulation run: {run_id}")
        return {"id": run_id, **run_info}


    def get_results(self, run_id, include=None, wait_for_completion=True, poll_interval=2):
        """Fetch output variables once simulation finishes."""
        include_qs = None
        if include:
            if isinstance(include, (list, tuple)):
                include_qs = ",".join(include)
            else:
                include_qs = str(include)
        url = f"{self.base_url}/model/run/{run_id}"
        if include_qs:
            url = f"{url}?include={include_qs}"
        while wait_for_completion:
            response = self.session.get(url)
            if response.status_code == 200:
                try:
                    data = response.json()
                    if data:
                        if isinstance(data, dict):
                            if "values" in data and isinstance(data["values"], dict):
                                return data["values"]
                            if "include" in data and isinstance(data["include"], dict):
                                return data["include"]
                        return data
                except Exception:
                    print("⚠️ Non-JSON response while waiting, retrying...")
            else:
                print(f"⚠️ Waiting... Status={response.status_code}")
            time.sleep(poll_interval)
        response.raise_for_status()
        return response.json()



class ExecutiveBot:
    """Board-level executive agent focusing on a KPI."""
    def __init__(self, name, kpi_focus, target=None, personality=None):
        self.name = name
        self.kpi_focus = kpi_focus
        self.target = target or {}
        self.personality = personality or {
            "risk_tolerance": 0.5,
            "friendliness": 0.5,
            "ambition": 0.5
        }

    def evaluate(self, results):
        """Judge simulation outputs according to role focus and personality."""
        kpi_value = results.get(self.kpi_focus, None)
        if kpi_value is None:
            return f"{self.name}: KPI {self.kpi_focus} not found."

        status = "on target"
        if self.target:
            if kpi_value < self.target.get("min", float("-inf")):
                status = "below target"
            elif kpi_value > self.target.get("max", float("inf")):
                status = "above target"

        return f"{self.name} sees {self.kpi_focus}={kpi_value}, status={status}"


class BoardRoom:
    """Simulates a meeting of bots discussing simulation results."""
    def __init__(self, bots):
        self.bots = bots

    def run_meeting(self, results):
        """Let all bots evaluate the simulation run."""
        return [bot.evaluate(results) for bot in self.bots]

    def simulate_interaction(self, setting="collaborative"):
        """Simplified placeholder for bot dynamics."""
        if setting == "collaborative":
            return "Bots align toward compromise."
        elif setting == "hostile":
            return "Bots argue, no consensus."
        else:
            return "Neutral interaction."

def plot_kpis(results_list, labels, kpis):
    fig, ax = plt.subplots(figsize=(8, 4))
    x = range(len(labels))
    width = 0.8 / max(1, len(kpis))
    for idx, k in enumerate(kpis):
        vals = [res.get(k, float("nan")) if isinstance(res, dict) else float("nan") for res in results_list]
        ax.bar([i + idx * width for i in x], vals, width=width, label=k)
    ax.set_xticks([i + (len(kpis)-1)*width/2 for i in x])
    ax.set_xticklabels(labels)
    ax.legend()
    ax.set_title("Agent KPI Comparison")
    plt.tight_layout()
    plt.show()


# === Sample Workflow ===
if __name__ == "__main__":
    client = ForioClient(
        org=FORIO_ORG,
        project=FORIO_PROJECT,
        model=FORIO_MODEL,
        public_key=PUBLIC_KEY,
        private_key=PRIVATE_KEY
    )

    params = {"prevention_budget": 50, "detection_budget": 30, "response_budget": 20}
    run = client.run_simulation(params)
    include_vars = ["accumulated_profit", "compromised_systems", "systems_availability"]
    results = client.get_results(run["id"], include=include_vars)

    cfo = ExecutiveBot("CFO", "accumulated_profit", target={"min": 1000000})
    cro = ExecutiveBot("CRO", "compromised_systems", target={"max": 10})
    coo = ExecutiveBot("COO", "systems_availability", target={"min": 0.95})

    board = BoardRoom([cfo, cro, coo])
    feedback = board.run_meeting(results)

    print("\n📊 Board Feedback:")
    for f in feedback:
        print(" -", f)

    print("\n🧠 Interaction:", board.simulate_interaction("collaborative"))
    try:
        plot_kpis([results], ["Strategy A"], include_vars)
    except Exception:
        pass
