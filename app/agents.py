"""
Executive Agent Classes
Single source of truth for agent behavior.
"""

import os
import json
from typing import List, Dict, Optional


class ExecutiveBot:
    """Board-level executive agent focusing on a specific KPI."""
    
    def __init__(self, name: str, kpi_focus: str, target: Dict = None, personality: Dict = None):
        self.name = name
        self.kpi_focus = kpi_focus
        self.target = target or {}
        self.personality = personality or {
            "risk_tolerance": 0.5,
            "friendliness": 0.5,
            "ambition": 0.5
        }
    
    def evaluate(self, results: Dict) -> str:
        """Evaluate simulation results based on this bot's KPI and personality."""
        kpi_value = results.get(self.kpi_focus)
        
        if kpi_value is None:
            return f"{self.name}: KPI '{self.kpi_focus}' not found in results"
        
        status = "on target"
        target_min = self.target.get("min", float("-inf"))
        target_max = self.target.get("max", float("inf"))
        
        if kpi_value < target_min:
            status = "below target"
        elif kpi_value > target_max:
            status = "above target"
        
        comment = self._get_personality_comment(status, kpi_value)
        
        if isinstance(kpi_value, float):
            if kpi_value < 1 and kpi_value > 0:
                value_str = f"{kpi_value:.1%}"
            else:
                value_str = f"{kpi_value:,.2f}"
        else:
            value_str = f"{kpi_value:,}"
        
        return f"{self.name} sees {self.kpi_focus}={value_str}, status={status}{comment}"
    
    def _get_personality_comment(self, status: str, kpi_value: float) -> str:
        """Generate personality-driven commentary."""
        comments = []
        
        if status == "below target":
            if self.personality["risk_tolerance"] > 0.7:
                comments.append(" (willing to take aggressive action)")
            elif self.personality["risk_tolerance"] < 0.3:
                comments.append(" (cautious, prefers gradual improvements)")
            
            if self.personality["ambition"] > 0.8:
                comments.append(" (pushing hard for improvement)")
        
        elif status == "above target":
            if self.personality["risk_tolerance"] < 0.3:
                comments.append(" (concerned about sustainability)")
            elif self.personality["ambition"] > 0.8:
                comments.append(" (wants even higher targets)")
        
        else:
            if self.personality["friendliness"] > 0.7:
                comments.append(" (satisfied with team performance)")
        
        return " ".join(comments)
    
    def recommend(self, results: Dict) -> str:
        """Provide strategic recommendation based on results."""
        kpi_value = results.get(self.kpi_focus)
        
        if kpi_value is None:
            return f"{self.name}: Cannot recommend without {self.kpi_focus} data"
        
        target_min = self.target.get("min", float("-inf"))
        target_max = self.target.get("max", float("inf"))
        
        if kpi_value < target_min:
            if self.personality["risk_tolerance"] > 0.6:
                return f"{self.name}: Increase investment aggressively to reach target"
            else:
                return f"{self.name}: Gradual increase recommended to reach target"
        
        elif kpi_value > target_max:
            return f"{self.name}: Reduce spending and optimize efficiency"
        
        else:
            if self.personality["ambition"] > 0.7:
                return f"{self.name}: Maintain strategy but explore optimization opportunities"
            else:
                return f"{self.name}: Maintain current strategy"


class BoardRoom:
    """Simulates board meeting with multiple executive agents."""
    
    def __init__(self, bots: List[ExecutiveBot]):
        self.bots = bots
    
    def run_meeting(self, results: Dict) -> List[str]:
        """Have all bots evaluate the results."""
        return [bot.evaluate(results) for bot in self.bots]
    
    def negotiate_strategy(self, results: Dict) -> List[str]:
        """Have all bots provide recommendations."""
        return [bot.recommend(results) for bot in self.bots]
    
    def simulate_interaction(self, setting: str = "collaborative") -> str:
        """
        Simulate board dynamics based on setting.
        
        Args:
            setting: 'collaborative', 'hostile', or 'neutral'
        """
        if setting == "collaborative":
            avg_friendliness = sum(b.personality["friendliness"] for b in self.bots) / len(self.bots)
            if avg_friendliness > 0.7:
                return "Bots work together constructively, finding common ground and shared strategy."
            else:
                return "Bots align toward compromise, though some tension remains."
        
        elif setting == "hostile":
            return "Bots argue over priorities, each defending their domain. No consensus reached."
        
        else:  # neutral
            return "Professional interaction. Each bot focuses on their own KPIs."


def load_agent_config(config_file: str = "config/agent_config.json") -> Dict:
    """Load agent configuration from JSON file."""
    
    default_config = {
        "CFO": {
            "kpi": "accumulated_profit",
            "target": {"min": 1200000},
            "personality": {
                "risk_tolerance": 0.3,
                "friendliness": 0.6,
                "ambition": 0.8
            }
        },
        "CRO": {
            "kpi": "compromised_systems",
            "target": {"max": 10},
            "personality": {
                "risk_tolerance": 0.2,
                "friendliness": 0.5,
                "ambition": 0.6
            }
        },
        "COO": {
            "kpi": "systems_availability",
            "target": {"min": 0.92},
            "personality": {
                "risk_tolerance": 0.5,
                "friendliness": 0.7,
                "ambition": 0.7
            }
        },
        "IT_Manager": {
            "kpi": "compromised_systems",
            "target": {"max": 8},
            "personality": {
                "risk_tolerance": 0.25,
                "friendliness": 0.6,
                "ambition": 0.7
            }
        },
        "CHRO": {
            "kpi": "systems_availability",
            "target": {"min": 0.93},
            "personality": {
                "risk_tolerance": 0.4,
                "friendliness": 0.75,
                "ambition": 0.65
            }
        }
    }
    
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            
            if 'agents' in config:
                config = config['agents']
            
            return config
        except Exception as e:
            print(f"Warning: Could not load config from {config_file}: {e}")
            print("Using default configuration")
    
    return default_config


def save_agent_config(config: Dict, config_file: str = "config/agent_config.json"):
    """Save agent configuration to JSON file."""
    os.makedirs(os.path.dirname(config_file), exist_ok=True)
    
    with open(config_file, 'w') as f:
        json.dump({"agents": config}, f, indent=2)
    
    print(f"Saved agent configuration to {config_file}")


if __name__ == '__main__':
    print("=" * 70)
    print("Agent Configuration Test")
    print("=" * 70)
    
    # Load configuration
    config = load_agent_config()
    
    print("\nAgent Configuration:")
    for name, settings in config.items():
        print(f"\n{name}:")
        print(f"  KPI: {settings['kpi']}")
        print(f"  Target: {settings['target']}")
        print(f"  Personality:")
        for trait, value in settings['personality'].items():
            bar = "█" * int(value * 20) + "░" * (20 - int(value * 20))
            print(f"    {trait:20s}: {bar} {value:.2f}")
    
    # Create agents
    print("\nCreating Agents:")
    agents = []
    for name, settings in config.items():
        agent = ExecutiveBot(
            name=name,
            kpi_focus=settings['kpi'],
            target=settings['target'],
            personality=settings['personality']
        )
        agents.append(agent)
        print(f"  {name}")
    
    # Test with sample data
    print("\nTesting with Sample Data:")
    sample_run = {
        "accumulated_profit": 1500000,
        "compromised_systems": 8,
        "systems_availability": 0.94
    }
    
    board = BoardRoom(agents)
    feedback = board.run_meeting(sample_run)
    
    print("\nEvaluations:")
    for comment in feedback:
        print(f"  {comment}")
    
    print("\nRecommendations:")
    recommendations = board.negotiate_strategy(sample_run)
    for rec in recommendations:
        print(f"  {rec}")
    
    print(f"\nBoard Dynamics: {board.simulate_interaction('collaborative')}")