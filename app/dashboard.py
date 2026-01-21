"""
Multi-Agent Dashboard - Compatible with Tailwind Template
"""

from flask import Flask, render_template, jsonify, request
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.agents import ExecutiveBot, BoardRoom, load_agent_config
from data.data_loader import (
    load_runs, 
    get_data_source_info, 
    load_csv_data,
    load_manual_data,
    generate_mock_data,
    compare_runs
)

app = Flask(__name__, 
           template_folder='../templates',
           static_folder='../static')

# Initialize bots from config
agent_config = load_agent_config()
bots = []

for name, config in agent_config.items():
    bot = ExecutiveBot(
        name=name,
        kpi_focus=config['kpi'],
        target=config['target'],
        personality=config['personality']
    )
    bots.append(bot)

board = BoardRoom(bots)


@app.route('/')
def index():
    """Main dashboard page."""
    return render_template('dashboard.html')


@app.route('/api/forio/status')
def api_forio_status():
    """Check Forio connection status (compatibility endpoint)."""
    sources = get_data_source_info()
    
    has_csv = sources['csv']['available']
    csv_count = sources['csv']['count']
    
    return jsonify({
        'connected': has_csv,
        'run_count': csv_count,
        'source': 'csv' if has_csv else 'mock'
    })


@app.route('/api/bots')
def api_bots():
    """Get bot information."""
    bots_info = []
    for bot in board.bots:
        bots_info.append({
            'name': bot.name,
            'kpi_focus': bot.kpi_focus,
            'target': bot.target,
            'personality': bot.personality
        })
    return jsonify(bots_info)


@app.route('/api/runs')
def api_runs():
    """Get simulated/bot runs (manual or mock data)."""
    manual = load_manual_data()
    
    # If no manual data, generate mock data
    if not manual:
        manual = generate_mock_data(20)
    
    # Format for the template
    formatted_runs = []
    for run in manual:
        formatted_runs.append({
            'id': run.get('id', ''),
            'strategy': run.get('strategy', f"Run {run.get('id', '')}"),
            'prevention_budget': run.get('security_investment', run.get('prevention_budget', 0)),
            'detection_budget': run.get('detection_budget', run.get('security_investment', 0) // 2),
            'response_budget': run.get('response_budget', run.get('recovery_cost', 0)),
            'accumulated_profit': run.get('accumulated_profit', 0),
            'compromised_systems': run.get('compromised_systems', 0),
            'systems_availability': run.get('systems_availability', 0.95)
        })
    
    return jsonify(formatted_runs)


@app.route('/api/real-data')
def api_real_data():
    """Get real data from CSV."""
    real_runs = load_csv_data()
    
    if not real_runs:
        return jsonify({'error': 'No real data available'}), 404
    
    # Format for the template
    formatted_runs = []
    for run in real_runs:
        formatted_runs.append({
            'id': run.get('id', ''),
            'strategy': f"Real Data - {run.get('id', '')}",
            'prevention_budget': run.get('security_investment', 0),
            'detection_budget': run.get('detection_budget', run.get('security_investment', 0) // 2),
            'response_budget': run.get('recovery_cost', 0),
            'accumulated_profit': run.get('accumulated_profit', 0),
            'compromised_systems': run.get('compromised_systems', 0),
            'systems_availability': run.get('systems_availability', 0.95)
        })
    
    return jsonify(formatted_runs)


@app.route('/api/evaluate', methods=['POST'])
def api_evaluate():
    """Evaluate a run with personality bots."""
    data = request.json
    run_data = data.get('run', {})
    
    # Get bot evaluations
    feedback = board.run_meeting(run_data)
    recommendations = board.negotiate_strategy(run_data)
    interaction = board.simulate_interaction('collaborative')
    
    return jsonify({
        'feedback': feedback,
        'recommendations': recommendations,
        'interaction': interaction
    })


@app.route('/api/compare-real')
def api_compare_real():
    """Compare real data against bot data."""
    try:
        # Load real and bot data
        real_runs = load_csv_data()
        bot_runs = load_manual_data()
        
        if not bot_runs:
            bot_runs = generate_mock_data(20)
        
        if not real_runs:
            return jsonify({'error': 'No real data available'}), 404
        
        # Find best performers in each dataset
        best_real_profit = max(real_runs, key=lambda r: r.get('accumulated_profit', 0))
        best_real_security = min(real_runs, key=lambda r: r.get('compromised_systems', float('inf')))
        best_real_availability = max(real_runs, key=lambda r: r.get('systems_availability', 0))
        
        best_bot_profit = max(bot_runs, key=lambda r: r.get('accumulated_profit', 0))
        best_bot_security = min(bot_runs, key=lambda r: r.get('compromised_systems', float('inf')))
        best_bot_availability = max(bot_runs, key=lambda r: r.get('systems_availability', 0))
        
        # Calculate averages
        real_avg = _calculate_average_run(real_runs)
        bot_avg = _calculate_average_run(bot_runs)
        
        # Get detailed comparison
        detailed_comparison = compare_runs(real_runs, bot_runs)
        
        return jsonify({
            'best_real_profit': {
                'accumulated_profit': best_real_profit.get('accumulated_profit', 0),
                'compromised_systems': best_real_profit.get('compromised_systems', 0),
                'systems_availability': best_real_profit.get('systems_availability', 0)
            },
            'best_real_security': {
                'accumulated_profit': best_real_security.get('accumulated_profit', 0),
                'compromised_systems': best_real_security.get('compromised_systems', 0),
                'systems_availability': best_real_security.get('systems_availability', 0)
            },
            'best_real_availability': {
                'accumulated_profit': best_real_availability.get('accumulated_profit', 0),
                'compromised_systems': best_real_availability.get('compromised_systems', 0),
                'systems_availability': best_real_availability.get('systems_availability', 0)
            },
            'best_bot_profit': {
                'accumulated_profit': best_bot_profit.get('accumulated_profit', 0),
                'compromised_systems': best_bot_profit.get('compromised_systems', 0),
                'systems_availability': best_bot_profit.get('systems_availability', 0)
            },
            'best_bot_security': {
                'accumulated_profit': best_bot_security.get('accumulated_profit', 0),
                'compromised_systems': best_bot_security.get('compromised_systems', 0),
                'systems_availability': best_bot_security.get('systems_availability', 0)
            },
            'best_bot_availability': {
                'accumulated_profit': best_bot_availability.get('accumulated_profit', 0),
                'compromised_systems': best_bot_availability.get('compromised_systems', 0),
                'systems_availability': best_bot_availability.get('systems_availability', 0)
            },
            'real_avg': real_avg,
            'bot_avg': bot_avg,
            'detailed_comparison': detailed_comparison,
            'counts': {
                'real_runs': len(real_runs),
                'bot_runs': len(bot_runs)
            }
        })
    
    except Exception as e:
        print(f"Error in compare-real: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/statistics')
def api_statistics():
    """Get statistical summary of all data."""
    real_runs = load_csv_data()
    bot_runs = load_manual_data()
    
    if not bot_runs:
        bot_runs = generate_mock_data(20)
    
    stats = {
        'real_data': _calculate_statistics(real_runs) if real_runs else None,
        'bot_data': _calculate_statistics(bot_runs) if bot_runs else None,
        'data_sources': get_data_source_info()
    }
    
    return jsonify(stats)


def _calculate_average_run(runs: list) -> dict:
    """Calculate average values across all runs."""
    if not runs:
        return {}
    
    # Get all numeric fields
    numeric_fields = {}
    for run in runs:
        for key, value in run.items():
            if isinstance(value, (int, float)) and key not in ['id']:
                if key not in numeric_fields:
                    numeric_fields[key] = []
                numeric_fields[key].append(value)
    
    # Calculate averages
    avg_run = {}
    for field, values in numeric_fields.items():
        avg_run[field] = sum(values) / len(values)
    
    return avg_run


def _calculate_statistics(runs: list) -> dict:
    """Calculate statistics for a set of runs."""
    if not runs:
        return {}
    
    stats = {
        'count': len(runs),
        'metrics': {}
    }
    
    # Get all numeric fields
    numeric_fields = {}
    for run in runs:
        for key, value in run.items():
            if isinstance(value, (int, float)) and key not in ['id']:
                if key not in numeric_fields:
                    numeric_fields[key] = []
                numeric_fields[key].append(value)
    
    # Calculate statistics for each field
    for field, values in numeric_fields.items():
        stats['metrics'][field] = {
            'min': min(values),
            'max': max(values),
            'avg': sum(values) / len(values),
            'median': sorted(values)[len(values) // 2]
        }
    
    return stats


if __name__ == '__main__':
    print("=" * 70)
    print("🚀 Multi-Agent Dashboard with Tailwind UI")
    print("=" * 70)
    
    # Check data sources
    sources = get_data_source_info()
    
    print("\n📊 Data Sources:")
    print(f"   CSV (Real Data): {'✓' if sources['csv']['available'] else '✗'}")
    if sources['csv']['available']:
        print(f"      Path: {sources['csv']['path']}")
        print(f"      Runs: {sources['csv']['count']}")
    
    print(f"   Manual: {'✓' if sources['manual']['available'] else '✗'}")
    if sources['manual']['available']:
        print(f"      Files: {', '.join(sources['manual']['files'][:3])}")
        print(f"      Runs: {sources['manual']['count']}")
    
    print(f"   Mock: ✓ (fallback)")
    
    # Determine what will be used
    if sources['csv']['available']:
        print("\n✓ Real CSV data available for comparison")
        if sources['manual']['available']:
            print("✓ Manual bot runs available")
        else:
            print("No manual runs - using mock bot data")
    else:
        print("\nNo real CSV data found at data/sim_data.csv")
        print("   Dashboard will use mock data only")
    
    print(f"\nLoaded {len(board.bots)} agents:")
    for bot in board.bots:
        print(f"   • {bot.name}: {bot.kpi_focus}")
    
    app.run(debug=True, host='0.0.0.0', port=5000)