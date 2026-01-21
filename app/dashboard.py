"""
Multi-Agent Backend API - Production Ready
Designed for React frontend integration
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import sys
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

app = Flask(__name__)

CORS(app, resources={
    r"/api/*": {
        "origins": os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173").split(","),
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

try:
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
    logger.info(f"✓ Initialized {len(bots)} agents")
except Exception as e:
    logger.error(f"Error initializing agents: {e}")
    board = None
    bots = []

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint for monitoring."""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'service': 'agentic-research-backend'
    }), 200


@app.route('/api/info', methods=['GET'])
def api_info():
    """Get service information and capabilities."""
    sources = get_data_source_info()
    
    return jsonify({
        'service': 'agentic-research-backend',
        'version': '1.0.0',
        'timestamp': datetime.utcnow().isoformat(),
        'agents': {
            'count': len(bots),
            'list': [{'name': bot.name, 'kpi': bot.kpi_focus} for bot in bots]
        },
        'data_sources': {
            'csv': sources['csv']['available'],
            'manual': sources['manual']['available'],
            'mock': True
        }
    })


# =====================
# Agent Endpoints
# =====================


@app.route('/api/bots', methods=['GET'])
def api_bots():
    """Get bot information and configurations."""
    if not bots:
        return jsonify({'error': 'No agents loaded'}), 500
    
    bots_info = []
    for bot in board.bots:
        bots_info.append({
            'name': bot.name,
            'kpi_focus': bot.kpi_focus,
            'target': bot.target,
            'personality': bot.personality
        })
    return jsonify(bots_info)


# =====================
# Data Endpoints
# =====================


@app.route('/api/runs', methods=['GET'])
def api_runs():
    """Get simulated/bot runs (manual or mock data)."""
    try:
        manual = load_manual_data()
        
        # If no manual data, generate mock data
        if not manual:
            manual = generate_mock_data(20)
        
        # Format for the API
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
        
        return jsonify({
            'success': True,
            'count': len(formatted_runs),
            'data': formatted_runs
        })
    except Exception as e:
        logger.error(f"Error fetching runs: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/runs/real', methods=['GET'])
def api_real_data():
    """Get real data from CSV."""
    try:
        real_runs = load_csv_data()
        
        if not real_runs:
            return jsonify({'success': False, 'count': 0, 'data': []}), 200
        
        # Return the raw CSV data without reformatting
        # This preserves the actual column names: Cum. Profits, Comp. Systems, Level, Ransomware, Pay Ransom, etc.
        return jsonify({
            'success': True,
            'count': len(real_runs),
            'data': real_runs
        })
    except Exception as e:
        logger.error(f"Error fetching real data: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/evaluate', methods=['POST'])
def api_evaluate():
    """Evaluate a run with personality bots."""
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        run_data = data.get('run', {})
        
        if not board:
            return jsonify({'error': 'Agents not initialized'}), 500
        
        # Get bot evaluations
        feedback = board.run_meeting(run_data)
        recommendations = board.negotiate_strategy(run_data)
        interaction = board.simulate_interaction('collaborative')
        
        return jsonify({
            'success': True,
            'feedback': feedback,
            'recommendations': recommendations,
            'interaction': interaction
        })
    except Exception as e:
        logger.error(f"Error evaluating run: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/runs/compare', methods=['GET'])
def api_compare_real():
    """Compare real data against bot data."""
    try:
        # Load real and bot data
        real_runs = load_csv_data()
        bot_runs = load_manual_data()
        
        if not bot_runs:
            bot_runs = generate_mock_data(20)
        
        if not real_runs:
            return jsonify({'success': False, 'message': 'No real data available'}), 200
        
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
            'success': True,
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
        logger.error(f"Error in compare-real: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/statistics', methods=['GET'])
def api_statistics():
    """Get statistical summary of all data."""
    try:
        real_runs = load_csv_data()
        bot_runs = load_manual_data()
        
        if not bot_runs:
            bot_runs = generate_mock_data(20)
        
        stats = {
            'real_data': _calculate_statistics(real_runs) if real_runs else None,
            'bot_data': _calculate_statistics(bot_runs) if bot_runs else None,
            'data_sources': get_data_source_info()
        }
        
        return jsonify({
            'success': True,
            'data': stats
        })
    except Exception as e:
        logger.error(f"Error calculating statistics: {e}")
        return jsonify({'error': str(e)}), 500


# =====================
# Simulation Scenarios
# =====================

@app.route('/api/scenarios', methods=['GET'])
def get_scenarios():
    """Get available simulation scenarios."""
    scenarios = [
        {
            'id': 'simple_deterministic',
            'name': 'Simple Cyber Threats - Deterministic Attacker',
            'description': 'Facing simple cyber threats with a predictable attacker'
        },
        {
            'id': 'simple_unpredictable',
            'name': 'Simple Cyber Threats - Unpredictable Attacker',
            'description': 'Facing simple cyber threats with an unpredictable attacker'
        },
        {
            'id': 'ransomware',
            'name': 'Advanced Ransomware Attack',
            'description': 'Facing advanced cyber attacks (ransomware)'
        },
        {
            'id': 'ransomware_ransom',
            'name': 'Advanced Ransomware - With Ransom Payment',
            'description': 'Facing advanced ransomware attacks with ransom payment option'
        }
    ]
    return jsonify({
        'success': True,
        'scenarios': scenarios
    }), 200


@app.route('/api/simulate', methods=['POST'])
def run_simulation():
    """Run a multi-agent simulation with specified parameters."""
    try:
        data = request.json
        scenario = data.get('scenario', 'simple_deterministic')
        agent_collaboration = data.get('agent_collaboration', 'collaborative')  # collaborative or uncollaborative
        risk_tolerance = data.get('risk_tolerance', 0.5)  # 0-1, affects tolerance parameter
        num_years = data.get('num_years', 5)
        
        # Generate mock simulation results based on parameters
        # In production, this would run actual simulations
        mock_results = generate_mock_simulation_results(
            scenario=scenario,
            collaboration=agent_collaboration,
            risk_tolerance=risk_tolerance,
            years=num_years
        )
        
        return jsonify({
            'success': True,
            'simulation_id': f"sim_{scenario}_{agent_collaboration}",
            'parameters': {
                'scenario': scenario,
                'agent_collaboration': agent_collaboration,
                'risk_tolerance': risk_tolerance,
                'num_years': num_years
            },
            'results': mock_results
        }), 200
    except Exception as e:
        logger.error(f"Error running simulation: {e}")
        return jsonify({'error': str(e)}), 500


def generate_mock_simulation_results(scenario, collaboration, risk_tolerance, years):
    """Generate mock simulation results based on parameters."""
    import random
    
    # Base values that vary by scenario
    scenario_impact = {
        'simple_deterministic': {'profit_variance': 0.1, 'risk_variance': 0.05},
        'simple_unpredictable': {'profit_variance': 0.15, 'risk_variance': 0.1},
        'ransomware': {'profit_variance': 0.25, 'risk_variance': 0.2},
        'ransomware_ransom': {'profit_variance': 0.3, 'risk_variance': 0.25}
    }
    
    impact = scenario_impact.get(scenario, scenario_impact['simple_deterministic'])
    
    # Collaborative agents perform better
    collab_bonus = 1.2 if collaboration == 'collaborative' else 0.8
    
    # Risk tolerance affects results
    profit_base = 1500000 * collab_bonus * (0.7 + risk_tolerance * 0.6)
    risk_base = 20 * collab_bonus * (1.0 - risk_tolerance * 0.5)
    
    # Generate time-series data
    time_series = []
    for year in range(1, years + 1):
        noise_profit = random.gauss(0, impact['profit_variance'] * profit_base)
        noise_risk = random.gauss(0, impact['risk_variance'] * risk_base)
        
        time_series.append({
            'year': year,
            'accumulated_profit': max(0, profit_base + noise_profit),
            'systems_at_risk': max(0, risk_base + noise_risk),
            'compromised_systems': max(0, (risk_base + noise_risk) / 2),
            'systems_availability': min(1.0, 0.95 - (risk_base + noise_risk) / 200)
        })
    
    return {
        'time_series': time_series,
        'summary': {
            'final_profit': time_series[-1]['accumulated_profit'],
            'final_risk': time_series[-1]['systems_at_risk'],
            'avg_availability': sum(t['systems_availability'] for t in time_series) / years,
            'scenario': scenario,
            'collaboration': collaboration,
            'risk_tolerance': risk_tolerance
        }
    }


# =====================
# Error Handlers
# =====================

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({
        'error': 'Endpoint not found',
        'status': 404,
        'timestamp': datetime.utcnow().isoformat()
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    logger.error(f"Internal server error: {error}")
    return jsonify({
        'error': 'Internal server error',
        'status': 500,
        'timestamp': datetime.utcnow().isoformat()
    }), 500


# =====================
# Utility Functions
# =====================


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


# =====================
# MongoDB Threshold Endpoints
# =====================

@app.route('/api/thresholds', methods=['POST'])
def create_threshold():
    """Create a new threshold for an agent KPI."""
    try:
        from data.mongodb_client import ThresholdManager
        
        data = request.json
        threshold_id = ThresholdManager.create_threshold(
            agent_name=data.get('agent_name'),
            kpi_name=data.get('kpi_name'),
            min_value=data.get('min_value'),
            max_value=data.get('max_value'),
            target_value=data.get('target_value'),
            description=data.get('description', '')
        )
        
        if threshold_id:
            return jsonify({
                'success': True,
                'threshold_id': threshold_id,
                'message': 'Threshold created successfully'
            }), 201
        else:
            return jsonify({'error': 'Failed to create threshold'}), 500
    
    except Exception as e:
        logger.error(f"Error creating threshold: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/thresholds', methods=['GET'])
def get_thresholds():
    """Get all thresholds or filter by agent."""
    try:
        from data.mongodb_client import ThresholdManager
        
        agent_name = request.args.get('agent')
        
        if agent_name:
            thresholds = ThresholdManager.get_agent_thresholds(agent_name)
        else:
            thresholds = ThresholdManager.get_all_thresholds()
        
        return jsonify({
            'success': True,
            'count': len(thresholds),
            'thresholds': thresholds
        }), 200
    
    except Exception as e:
        logger.error(f"Error fetching thresholds: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/thresholds/<threshold_id>', methods=['GET'])
def get_threshold(threshold_id):
    """Get a specific threshold."""
    try:
        from data.mongodb_client import ThresholdManager
        
        threshold = ThresholdManager.get_threshold(threshold_id)
        
        if threshold:
            return jsonify({
                'success': True,
                'threshold': threshold
            }), 200
        else:
            return jsonify({'error': 'Threshold not found'}), 404
    
    except Exception as e:
        logger.error(f"Error fetching threshold: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/thresholds/<threshold_id>', methods=['PUT'])
def update_threshold(threshold_id):
    """Update a threshold."""
    try:
        from data.mongodb_client import ThresholdManager
        
        data = request.json
        success = ThresholdManager.update_threshold(threshold_id, **data)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Threshold updated successfully'
            }), 200
        else:
            return jsonify({'error': 'Failed to update threshold'}), 500
    
    except Exception as e:
        logger.error(f"Error updating threshold: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/thresholds/<threshold_id>', methods=['DELETE'])
def delete_threshold(threshold_id):
    """Delete a threshold."""
    try:
        from data.mongodb_client import ThresholdManager
        
        success = ThresholdManager.delete_threshold(threshold_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Threshold deleted successfully'
            }), 200
        else:
            return jsonify({'error': 'Failed to delete threshold'}), 500
    
    except Exception as e:
        logger.error(f"Error deleting threshold: {e}")
        return jsonify({'error': str(e)}), 500


# =====================
# Simulation Comparison Endpoints
# =====================

@app.route('/api/simulations/<simulation_id>/log', methods=['POST'])
def log_simulation_run(simulation_id):
    """Log a simulation run against a threshold."""
    try:
        from data.mongodb_client import SimulationComparator
        
        data = request.json
        run_id = SimulationComparator.log_simulation_run(
            simulation_id=simulation_id,
            threshold_id=data.get('threshold_id'),
            agent_name=data.get('agent_name'),
            kpi_name=data.get('kpi_name'),
            actual_value=data.get('actual_value'),
            target_value=data.get('target_value'),
            min_value=data.get('min_value'),
            max_value=data.get('max_value'),
            metadata=data.get('metadata')
        )
        
        if run_id:
            return jsonify({
                'success': True,
                'run_id': run_id,
                'message': 'Simulation run logged'
            }), 201
        else:
            return jsonify({'error': 'Failed to log simulation run'}), 500
    
    except Exception as e:
        logger.error(f"Error logging simulation run: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/simulations/<simulation_id>/results', methods=['GET'])
def get_simulation_results(simulation_id):
    """Get results for a specific simulation."""
    try:
        from data.mongodb_client import SimulationComparator
        
        results = SimulationComparator.get_simulation_results(simulation_id)
        
        return jsonify({
            'success': True,
            'simulation_id': simulation_id,
            'results': results
        }), 200
    
    except Exception as e:
        logger.error(f"Error fetching simulation results: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/simulations/<simulation_id>/compare', methods=['POST'])
def log_comparison(simulation_id):
    """Log a comparison result."""
    try:
        from data.mongodb_client import SimulationComparator
        
        data = request.json
        comparison_id = SimulationComparator.log_comparison(
            simulation_id=simulation_id,
            threshold_id=data.get('threshold_id'),
            is_within_threshold=data.get('is_within_threshold'),
            actual_value=data.get('actual_value'),
            threshold_min=data.get('threshold_min'),
            threshold_max=data.get('threshold_max'),
            notes=data.get('notes', '')
        )
        
        if comparison_id:
            return jsonify({
                'success': True,
                'comparison_id': comparison_id,
                'message': 'Comparison logged'
            }), 201
        else:
            return jsonify({'error': 'Failed to log comparison'}), 500
    
    except Exception as e:
        logger.error(f"Error logging comparison: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/thresholds/<threshold_id>/history', methods=['GET'])
def get_threshold_history(threshold_id):
    """Get comparison history for a threshold."""
    try:
        from data.mongodb_client import SimulationComparator
        
        limit = request.args.get('limit', default=100, type=int)
        history = SimulationComparator.get_comparison_history(threshold_id, limit)
        
        return jsonify({
            'success': True,
            'threshold_id': threshold_id,
            'count': len(history),
            'history': history
        }), 200
    
    except Exception as e:
        logger.error(f"Error fetching threshold history: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/statistics/thresholds', methods=['GET'])
def get_threshold_statistics():
    """Get statistics on threshold compliance."""
    try:
        from data.mongodb_client import SimulationComparator
        
        threshold_id = request.args.get('threshold_id')
        agent_name = request.args.get('agent')
        days = request.args.get('days', default=30, type=int)
        
        stats = SimulationComparator.get_statistics(
            threshold_id=threshold_id,
            agent_name=agent_name,
            days=days
        )
        
        return jsonify({
            'success': True,
            'statistics': stats
        }), 200
    
    except Exception as e:
        logger.error(f"Error fetching statistics: {e}")
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    import os
    
    # Get configuration from environment
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', 5001))
    debug = os.getenv('DEBUG', 'False').lower() == 'true'
    
    print("=" * 70)
    print("🚀 Agentic Research Backend - API Server")
    print("=" * 70)
    
    sources = get_data_source_info()
    
    print("\nData Sources:")
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
            print("ℹ No manual runs - using mock bot data")
    else:
        print("\nℹ No real CSV data found at data/sim_data.csv")
        print("   Dashboard will use mock data only")
    
    print(f"\nLoaded {len(bots)} agents:")
    for bot in bots:
        print(f"   • {bot.name}: {bot.kpi_focus}")
    
    print(f"\nAPI Server starting:")
    print(f"   URL: http://{host}:{port}")
    print(f"   Debug: {debug}")
    print(f"   CORS Origins: {os.getenv('CORS_ORIGINS', 'http://localhost:3000,http://localhost:5173')}")
    
    print("\nAPI Endpoints:")
    print("   GET  /health                    - Health check")
    print("   GET  /api/info                  - Service info")
    print("   GET  /api/bots                  - List agents")
    print("   GET  /api/runs                  - Get bot simulation runs")
    print("   GET  /api/runs/real             - Get real data")
    print("   POST /api/evaluate              - Evaluate a run")
    print("   GET  /api/runs/compare          - Compare real vs bot data")
    print("   GET  /api/statistics            - Statistical summary")
    
    print("\n" + "=" * 70)
    
    app.run(host=host, port=port, debug=debug)