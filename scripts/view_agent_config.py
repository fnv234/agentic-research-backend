"""
View Agent Configuration
Quick script to see current agent thresholds, targets, and personalities.
"""

from multi_agent_demo_mock import ExecutiveBot, BoardRoom

cfo = ExecutiveBot(
    "CFO", 
    "accumulated_profit", 
    target={"min": 1200000},
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
    target={"min": 0.92},
    personality={"risk_tolerance": 0.5, "friendliness": 0.7, "ambition": 0.7}
)

board = BoardRoom([cfo, cro, coo])


for bot in board.bots:
    print(f"\n{bot.name}")
    print("─" * 70)
    print(f"KPI Focus: {bot.kpi_focus}")
    print(f"Target: {bot.target}")
    
    # Show what the target means
    if "min" in bot.target:
        print(f"      → Must be >= {bot.target['min']:,}")
    if "max" in bot.target:
        print(f"      → Must be <= {bot.target['max']:,}")
    
    print(f"\n Personality:")
    for trait, value in bot.personality.items():
        bar_length = int(value * 20)
        bar = "█" * bar_length + "░" * (20 - bar_length)
        print(f"      {trait:20s}: {bar} {value:.2f}")

print("\n" + "=" * 70)
print("INTERPRETATION")
print("=" * 70)

print("\nTargets:")
print(f"  • CFO wants profit >= $1,200,000")
print(f"  • CRO wants compromised systems <= 10")
print(f"  • COO wants availability >= 92%")

print("\nPersonality Traits (0.0 - 1.0):")
print(f"  • Risk Tolerance: How aggressive vs cautious")
print(f"      Low (0.0-0.3): Very cautious, gradual changes")
print(f"      Mid (0.4-0.6): Balanced approach")
print(f"      High (0.7-1.0): Aggressive, big bets")
print(f"\n  • Friendliness: How collaborative vs confrontational")
print(f"      Low (0.0-0.3): Direct, confrontational")
print(f"      Mid (0.4-0.6): Professional")
print(f"      High (0.7-1.0): Collaborative, supportive")
print(f"\n  • Ambition: How satisfied vs demanding")
print(f"      Low (0.0-0.3): Satisfied with status quo")
print(f"      Mid (0.4-0.6): Moderate expectations")
print(f"      High (0.7-1.0): Always pushing for more")

print("\n" + "=" * 70)
print("🔧 TO MODIFY")
print("=" * 70)
print("\nEdit these files:")
print("  1. dashboard.py (lines 29-48) - for web dashboard")
print("  2. multi_agent_demo_mock.py (lines 202-221) - for standalone demo")
print("\nOr run calibration tool:")
print("  python calibrate_agents.py")
print()
