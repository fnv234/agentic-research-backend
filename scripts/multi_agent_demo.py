"""
Multi-Agent Demo using existing Forio simulation runs.
Since the project uses a facilitator interface, we'll fetch existing runs
and have agents evaluate them rather than creating new runs programmatically.
"""

import os
import base64
import requests
from dotenv import load_dotenv
import matplotlib.pyplot as plt

load_dotenv()
PUBLIC_KEY = os.getenv("PUBLIC_KEY")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
FORIO_ORG = os.getenv("FORIO_ORG", "mitcams")
FORIO_PROJECT = os.getenv("FORIO_PROJECT", "cyberriskmanagement-ransomeware-2023")


class ForioDataFetcher:
    """Fetches existing run data from Forio facilitator projects."""
    
    def __init__(self, org, project, public_key, private_key):
        self.org = org
        self.project = project
        self.token = self._get_oauth_token(public_key, private_key)
    
    def _get_oauth_token(self, public_key, private_key):
        creds = base64.b64encode(f"{public_key}:{private_key}".encode()).decode()
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Basic {creds}"
        }
        data = {"grant_type": "client_credentials"}
        r = requests.post("https://api.forio.com/v2/oauth/token", headers=headers, data=data)
        if r.status_code >= 400:
            raise RuntimeError(f"❌ OAuth error {r.status_code}: {r.text}")
        return r.json().get("access_token")
    
    def fetch_runs(self, group=None, include_vars=None, limit=10):
        """Fetch existing saved runs from the project."""
        headers = {"Authorization": f"Bearer {self.token}"}
        
        # Build query parameters
        group_filter = f"scope.group={group}" if group else ""
        include_str = ",".join(include_vars) if include_vars else ""
        
        url = f"https://forio.com/v2/run/{self.org}/{self.project}/;saved=true;trashed=false"
        if group_filter:
            url += f";{group_filter}"
        url += f"?sort=created&direction=desc&startRecord=0&endRecord={limit}"
        if include_str:
            url += f"&include={include_str}"
        
        print(f"🔗 GET {url}")
        response = requests.get(url, headers=headers)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            runs = response.json()
            # For each run, fetch variables separately if needed
            if include_vars and runs:
                for run in runs:
                    run_id = run.get('id')
                    if run_id:
                        var_url = f"https://api.forio.com/v2/model/run/{run_id}/variables"
                        if include_str:
                            var_url += f"?include={include_str}"
                        var_resp = requests.get(var_url, headers=headers)
                        if var_resp.status_code == 200:
                            run['variables'] = var_resp.json()
            return runs
        else:
            print(f"Error: {response.text}")
            return []


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
        # Handle nested result structures
        if isinstance(results, dict):
            kpi_value = results.get(self.kpi_focus)
            if kpi_value is None and "variables" in results:
                kpi_value = results["variables"].get(self.kpi_focus)
            if kpi_value is None and "values" in results:
                kpi_value = results["values"].get(self.kpi_focus)
        else:
            kpi_value = None
        
        if kpi_value is None:
            return f"{self.name}: KPI {self.kpi_focus} not found in results"
        
        status = "on target"
        if self.target:
            if kpi_value < self.target.get("min", float("-inf")):
                status = "below target"
            elif kpi_value > self.target.get("max", float("inf")):
                status = "above target"
        
        # Personality-driven commentary
        if self.personality["risk_tolerance"] > 0.7 and status == "below target":
            comment = "(willing to take risks to improve)"
        elif self.personality["risk_tolerance"] < 0.3 and status == "above target":
            comment = "(concerned about sustainability)"
        else:
            comment = ""
        
        return f"{self.name} sees {self.kpi_focus}={kpi_value:.2f}, status={status} {comment}"


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


def plot_kpis_comparison(runs_data, kpis, labels=None):
    """Plot KPIs across multiple runs for comparison."""
    if not runs_data:
        print("No data to plot")
        return
    
    if labels is None:
        labels = [f"Run {i+1}" for i in range(len(runs_data))]
    
    fig, axes = plt.subplots(1, len(kpis), figsize=(5*len(kpis), 4))
    if len(kpis) == 1:
        axes = [axes]
    
    for idx, kpi in enumerate(kpis):
        vals = []
        for run in runs_data:
            val = run.get(kpi)
            if val is None and "variables" in run:
                val = run["variables"].get(kpi)
            if val is None and "values" in run:
                val = run["values"].get(kpi)
            vals.append(val if val is not None else 0)
        
        axes[idx].bar(range(len(labels)), vals, color='steelblue')
        axes[idx].set_xticks(range(len(labels)))
        axes[idx].set_xticklabels(labels, rotation=45, ha='right')
        axes[idx].set_title(kpi.replace('_', ' ').title())
        axes[idx].set_ylabel('Value')
    
    plt.tight_layout()
    plt.savefig('kpi_comparison.png', dpi=150, bbox_inches='tight')
    print("📊 Plot saved to kpi_comparison.png")
    plt.show()


# === Demo Workflow ===
if __name__ == "__main__":
    print("🤖 Multi-Agent Simulation Analysis Demo\n")
    
    # Initialize data fetcher
    fetcher = ForioDataFetcher(
        org=FORIO_ORG,
        project=FORIO_PROJECT,
        public_key=PUBLIC_KEY,
        private_key=PRIVATE_KEY
    )
    
    # Fetch recent runs
    print("Fetching recent simulation runs...")
    kpis_to_fetch = ["accumulated_profit", "compromised_systems", "systems_availability"]
    runs = fetcher.fetch_runs(include_vars=kpis_to_fetch, limit=5)
    
    if not runs:
        print("\n⚠️  No saved runs found. Please run the simulation through the Forio facilitator interface first.")
        print(f"   Visit: https://forio.com/app/{FORIO_ORG}/{FORIO_PROJECT}/")
        exit(0)
    
    print(f"\n✅ Found {len(runs)} runs\n")
    
    # Create executive bots with different personalities
    cfo = ExecutiveBot(
        "CFO", 
        "accumulated_profit", 
        target={"min": 1000000},
        personality={"risk_tolerance": 0.3, "friendliness": 0.6, "ambition": 0.8}
    )
    cro = ExecutiveBot(
        "CRO", 
        "compromised_systems", 
        target={"max": 10},
        personality={"risk_tolerance": 0.2, "friendliness": 0.5, "ambition": 0.6}
    )
    coo = ExecutiveBot(
        "COO", 
        "systems_availability", 
        target={"min": 0.95},
        personality={"risk_tolerance": 0.5, "friendliness": 0.7, "ambition": 0.7}
    )
    
    board = BoardRoom([cfo, cro, coo])
    
    # Analyze each run
    for i, run in enumerate(runs[:3]):  # Analyze top 3 runs
        print(f"\n{'='*60}")
        print(f"📊 Analyzing Run {i+1} (ID: {run.get('id', 'unknown')[:20]}...)")
        print(f"{'='*60}")
        
        feedback = board.run_meeting(run)
        for comment in feedback:
            print(f"  • {comment}")
        
        print(f"\n🧠 Board Interaction: {board.simulate_interaction('collaborative')}")
    
    # Plot comparison
    print(f"\n{'='*60}")
    print("📈 Generating KPI comparison plot...")
    try:
        plot_kpis_comparison(runs[:5], kpis_to_fetch)
    except Exception as e:
        print(f"⚠️  Could not generate plot: {e}")
    
    print("\n✅ Analysis complete!")
