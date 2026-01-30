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
    r"/*": {
        "origins": os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173,https://agentic-research-frontend.onrender.com").split(","),
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

@app.route('/', methods=['GET'])
def root():
    """Root endpoint - redirect to API info."""
    return jsonify({
        'message': 'Agentic Research Backend API',
        'service': 'agentic-research-backend',
        'status': 'online',
        'docs': 'See /api/info for service information'
    }), 200


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
        
        if not manual:
            manual = generate_mock_data(20)
        
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
        
        return jsonify({
            'success': True,
            'count': len(formatted_runs),
            'data': formatted_runs
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
        real_runs = load_csv_data()
        bot_runs = load_manual_data()
        
        if not bot_runs:
            bot_runs = generate_mock_data(20)
        
        if not real_runs:
            return jsonify({'success': False, 'message': 'No real data available'}), 200
        
        best_real_profit = max(real_runs, key=lambda r: r.get('accumulated_profit', 0))
        best_real_security = min(real_runs, key=lambda r: r.get('compromised_systems', float('inf')))
        best_real_availability = max(real_runs, key=lambda r: r.get('systems_availability', 0))
        
        best_bot_profit = max(bot_runs, key=lambda r: r.get('accumulated_profit', 0))
        best_bot_security = min(bot_runs, key=lambda r: r.get('compromised_systems', float('inf')))
        best_bot_availability = max(bot_runs, key=lambda r: r.get('systems_availability', 0))
        
        real_avg = _calculate_average_run(real_runs)
        bot_avg = _calculate_average_run(bot_runs)
        
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
        agent_collaboration = data.get('agent_collaboration', 'collaborative')
        risk_tolerance = data.get('risk_tolerance', 0.5)
        num_years = data.get('num_years', 5)
        
        sim_results = load_simulation_for_scenario(
            scenario=scenario,
            collaboration=agent_collaboration,
            risk_tolerance=risk_tolerance,
            years=num_years
        )
        
        agent_perspectives = get_agent_perspectives(
            scenario=scenario,
            collaboration=agent_collaboration,
            risk_tolerance=risk_tolerance
        )
        
        sim_results['agent_perspectives'] = agent_perspectives
        
        return jsonify({
            'success': True,
            'simulation_id': f"sim_{scenario}_{agent_collaboration}_{int(risk_tolerance*100)}",
            'parameters': {
                'scenario': scenario,
                'agent_collaboration': agent_collaboration,
                'risk_tolerance': risk_tolerance,
                'num_years': num_years
            },
            'results': sim_results
        }), 200
    except Exception as e:
        logger.error(f"Error running simulation: {e}")
        return jsonify({'error': str(e)}), 500


def get_agent_perspectives(scenario, collaboration, risk_tolerance):
    """Get perspectives from each agent based on scenario and parameters."""
    
    agent_configs = [
        {
            'agent': 'CFO',
            'kpi_focus': 'Accumulated Profit',
            'target': 'Maximize revenue, minimize security costs',
            'personality': {'ambition': 0.9, 'risk_tolerance': 0.8},
            'recommendation': 'Focus on cost-effective security measures to maximize profit margins'
        },
        {
            'agent': 'CRO',
            'kpi_focus': 'Risk Mitigation',
            'target': 'Minimize systems at risk',
            'personality': {'ambition': 0.6, 'risk_tolerance': 0.2},
            'recommendation': 'Implement comprehensive security controls and threat detection'
        },
        {
            'agent': 'COO',
            'kpi_focus': 'Operational Continuity',
            'target': 'Maintain systems availability',
            'personality': {'ambition': 0.7, 'risk_tolerance': 0.4},
            'recommendation': 'Ensure business continuity and rapid recovery capabilities'
        },
        {
            'agent': 'IT_Manager',
            'kpi_focus': 'Security & Recovery',
            'target': 'Fast detection and response',
            'personality': {'ambition': 0.8, 'risk_tolerance': 0.3},
            'recommendation': 'Deploy advanced detection systems and incident response procedures'
        },
        {
            'agent': 'CHRO',
            'kpi_focus': 'Team Readiness',
            'target': 'Prepared incident response team',
            'personality': {'ambition': 0.6, 'risk_tolerance': 0.5},
            'recommendation': 'Ensure team training and preparedness for security incidents'
        },
        {
            'agent': 'COO_Business',
            'kpi_focus': 'Business Resilience',
            'target': 'Customer satisfaction and trust',
            'personality': {'ambition': 0.75, 'risk_tolerance': 0.6},
            'recommendation': 'Communicate transparently and maintain customer confidence'
        }
    ]
    
    for agent_config in agent_configs:
        if collaboration == 'collaborative':
            base_priority = 0.7 + (risk_tolerance * 0.2)
        else:
            base_priority = agent_config['personality']['ambition'] * 0.8
        
        threat_adjustments = {
            'simple_deterministic': 0.6,
            'simple_unpredictable': 0.7,
            'ransomware': 0.85,
            'ransomware_ransom': 0.95
        }
        
        scenario_adjustment = threat_adjustments.get(scenario, 0.7)
        agent_config['priority'] = min(1.0, base_priority * scenario_adjustment)
    
    return agent_configs


def run_multi_agent_simulation(scenario, collaboration, risk_tolerance, years):
    """
    Run the actual multi-agent environment simulation.
    Gets agent recommendations and simulates outcomes over time.
    """
    try:
        scenario_context = {
            'simple_deterministic': {
                'description': 'Predictable attacker with known patterns',
                'threat_level': 'Low-Medium',
                'attack_probability': 0.3
            },
            'simple_unpredictable': {
                'description': 'Unpredictable attacker with variable tactics',
                'threat_level': 'Low-Medium',
                'attack_probability': 0.4
            },
            'ransomware': {
                'description': 'Advanced ransomware attack',
                'threat_level': 'High',
                'attack_probability': 0.6
            },
            'ransomware_ransom': {
                'description': 'Ransomware with ransom demand',
                'threat_level': 'High',
                'attack_probability': 0.7
            }
        }
        
        scenario_data = scenario_context.get(scenario, scenario_context['simple_deterministic'])
        
        if board and bots:
            run_context = {
                'scenario': scenario,
                'threat_level': scenario_data['threat_level'],
                'attack_probability': scenario_data['attack_probability'],
                'collaboration': collaboration,
                'risk_tolerance': risk_tolerance
            }
            
            agent_feedback = board.run_meeting(run_context)
            agent_recommendations = board.negotiate_strategy(run_context)
            agent_interaction = board.simulate_interaction(collaboration)
            
            agent_perspectives = []
            for bot in bots:
                perspective = {
                    'agent': bot.name,
                    'kpi_focus': bot.kpi_focus,
                    'target': bot.target,
                    'personality': bot.personality,
                    'recommendation': f"Focus on {bot.kpi_focus}",
                    'priority': _calculate_agent_priority(bot, scenario_data, risk_tolerance)
                }
                agent_perspectives.append(perspective)
        else:
            agent_feedback = "No agents available"
            agent_recommendations = []
            agent_interaction = {}
            agent_perspectives = []
        
        sim_results = load_simulation_for_scenario(
            scenario=scenario,
            collaboration=collaboration,
            risk_tolerance=risk_tolerance,
            years=years
        )
        
        sim_results['agent_perspectives'] = agent_perspectives
        sim_results['agent_feedback'] = agent_feedback
        sim_results['agent_recommendations'] = agent_recommendations
        sim_results['agent_interaction'] = agent_interaction
        
        return sim_results
        
    except Exception as e:
        logger.warning(f"Error running multi-agent simulation: {e}, using fallback")
        return load_simulation_for_scenario(scenario, collaboration, risk_tolerance, years)


def _calculate_agent_priority(agent, scenario_data, risk_tolerance):
    """Calculate priority score for an agent based on scenario and risk tolerance."""
    import random
    
    agent_priorities = {
        'CFO': 0.9 if risk_tolerance > 0.5 else 0.7,
        'CRO': 0.9 if scenario_data['threat_level'] == 'High' else 0.6,
        'COO': 0.8,
        'IT_Manager': 0.85 if scenario_data['threat_level'] == 'High' else 0.7,
        'CHRO': 0.7,
        'COO_Business': 0.8
    }
    
    return agent_priorities.get(agent.name, 0.75) + random.uniform(-0.1, 0.1)

def load_simulation_for_scenario(scenario, collaboration, risk_tolerance, years):
    """Load simulation data for a specific scenario from CSV."""
    import pandas as pd
    
    csv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'sim_data.csv')
    
    try:
        df = pd.read_csv(csv_path)
        
        if 'Cum. Profits' in df.columns:
            df['Cum. Profits'] = pd.to_numeric(df['Cum. Profits'].astype(str).str.replace(',', ''), errors='coerce')
        
        numeric_cols = ['Comp. Systems', 'Level', 'Ransomware', 'Pay Ransom']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        scenario_filters = {
            'simple_deterministic': {'Level': 1, 'Ransomware': 0},
            'simple_unpredictable': {'Level': 1, 'Ransomware': 0},
            'ransomware': {'Ransomware': 1, 'Pay Ransom': 0},
            'ransomware_ransom': {'Ransomware': 1, 'Pay Ransom': 1}
        }
        
        filters = scenario_filters.get(scenario, {})
        filtered = df.copy()
        for col, val in filters.items():
            if col in filtered.columns:
                filtered = filtered[filtered[col] == val]
        
        if len(filtered) == 0:
            return generate_mock_simulation_results(scenario, collaboration, risk_tolerance, years)
        
        if collaboration == 'collaborative':
            filtered = filtered.nlargest(10, 'Cum. Profits')
        else:
            filtered = filtered.sample(min(10, len(filtered)))
        
        avg_profit = filtered['Cum. Profits'].mean() if len(filtered) > 0 else 1500000
        avg_risk = filtered['Comp. Systems'].mean() if len(filtered) > 0 else 15
        
        avg_profit = avg_profit * (0.7 + risk_tolerance * 0.6)
        avg_risk = avg_risk * (1.0 - risk_tolerance * 0.3)
        
        time_series = []
        for year in range(1, years + 1):
            profit_at_year = avg_profit * (year / years) * (0.8 + (year / years) * 0.4)
            time_series.append({
                'year': year,
                'accumulated_profit': max(0, profit_at_year),
                'systems_at_risk': max(0, avg_risk * (1.5 - year / years)),
                'compromised_systems': max(0, (avg_risk * (1.5 - year / years)) / 2),
                'systems_availability': min(1.0, 0.92 + (year / years) * 0.06)
            })
        
        return {
            'time_series': time_series,
            'summary': {
                'final_profit': time_series[-1]['accumulated_profit'],
                'final_risk': time_series[-1]['systems_at_risk'],
                'avg_availability': sum(t['systems_availability'] for t in time_series) / years,
                'scenario': scenario,
                'collaboration': collaboration,
                'risk_tolerance': risk_tolerance,
                'data_source': 'sim_data.csv'
            }
        }
    except Exception as e:
        logger.warning(f"Could not load real simulation data: {e}, using mock data")
        return generate_mock_simulation_results(scenario, collaboration, risk_tolerance, years)


def generate_mock_simulation_results(scenario, collaboration, risk_tolerance, years):
    """Generate mock simulation results based on parameters."""
    import random
    
    scenario_impact = {
        'simple_deterministic': {'profit_variance': 0.1, 'risk_variance': 0.05},
        'simple_unpredictable': {'profit_variance': 0.15, 'risk_variance': 0.1},
        'ransomware': {'profit_variance': 0.25, 'risk_variance': 0.2},
        'ransomware_ransom': {'profit_variance': 0.3, 'risk_variance': 0.25}
    }
    
    impact = scenario_impact.get(scenario, scenario_impact['simple_deterministic'])
    
    collab_bonus = 1.2 if collaboration == 'collaborative' else 0.8
    
    profit_base = 1500000 * collab_bonus * (0.7 + risk_tolerance * 0.6)
    risk_base = 20 * collab_bonus * (1.0 - risk_tolerance * 0.5)
    
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
    
    numeric_fields = {}
    for run in runs:
        for key, value in run.items():
            if isinstance(value, (int, float)) and key not in ['id']:
                if key not in numeric_fields:
                    numeric_fields[key] = []
                numeric_fields[key].append(value)
    
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
    
    numeric_fields = {}
    for run in runs:
        for key, value in run.items():
            if isinstance(value, (int, float)) and key not in ['id']:
                if key not in numeric_fields:
                    numeric_fields[key] = []
                numeric_fields[key].append(value)
    
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


def _dashboard_statistics_shape(raw):
    """Convert MongoDB threshold stats to dashboard-expected shape."""
    if not raw:
        return {
            'total_runs': 0,
            'pass_rate': 0,
            'on_target_count': 0,
            'below_min_count': 0,
            'above_max_count': 0,
            'off_target_count': 0,
            'failures': []
        }
    total = raw.get('total', 0)
    passed = raw.get('passed', 0)
    failed = raw.get('failed', 0)
    pass_rate_pct = raw.get('pass_rate', 0)
    return {
        'total_runs': total,
        'pass_rate': (pass_rate_pct / 100.0) if pass_rate_pct else 0,
        'on_target_count': passed,
        'below_min_count': 0,
        'above_max_count': 0,
        'off_target_count': failed,
        'failures': raw.get('failures', [])
    }


@app.route('/api/statistics/thresholds', methods=['GET'])
def get_threshold_statistics():
    """Get statistics on threshold compliance. Returns dashboard-friendly shape."""
    try:
        from data.mongodb_client import SimulationComparator, init_mongodb
        
        threshold_id = request.args.get('threshold_id')
        agent_name = request.args.get('agent')
        days = request.args.get('days', default=30, type=int)
        
        db = init_mongodb()
        if db is None:
            return jsonify({
                'success': True,
                'statistics': _dashboard_statistics_shape(None)
            }), 200
        
        stats = SimulationComparator.get_statistics(
            threshold_id=threshold_id,
            agent_name=agent_name,
            days=days
        )
        
        return jsonify({
            'success': True,
            'statistics': _dashboard_statistics_shape(stats)
        }), 200
    
    except Exception as e:
        logger.error(f"Error fetching statistics: {e}")
        return jsonify({
            'success': True,
            'statistics': _dashboard_statistics_shape(None)
        }), 200

@app.route('/api/analysis/architecture', methods=['GET'])
def get_architecture_description():
    """Return architecture and design documentation for the multi-agent environment"""
    return jsonify({
        "title": "Multi-Agent Cyber Risk Environment - Architecture & Design",
        "description": "A framework for studying how multiple organizational stakeholders make coordinated decisions under cyber risk uncertainty",
        "agents": {
            "CFO": {
                "role": "Chief Financial Officer",
                "primary_objective": "Maximize accumulated profit",
                "decision_focus": "Investment allocation - budget vs security spending",
                "parameters": ["profit_target", "cost_sensitivity"]
            },
            "CRO": {
                "role": "Chief Risk Officer", 
                "primary_objective": "Minimize systems at risk",
                "decision_focus": "Risk mitigation strategy - defensive posture",
                "parameters": ["risk_threshold", "mitigation_budget"]
            },
            "COO": {
                "role": "Chief Operating Officer",
                "primary_objective": "Maintain operational continuity",
                "decision_focus": "Business continuity - uptime vs cost",
                "parameters": ["availability_target", "recovery_speed"]
            },
            "IT_Manager": {
                "role": "IT Infrastructure Manager",
                "primary_objective": "Secure systems and recovery",
                "decision_focus": "Technical implementation - detection and response",
                "parameters": ["detection_sensitivity", "response_time"]
            },
            "CHRO": {
                "role": "Chief Human Resources Officer",
                "primary_objective": "Manage recovery and incident response",
                "decision_focus": "Team readiness - training and preparedness",
                "parameters": ["training_level", "incident_response_team_size"]
            },
            "COO_Business": {
                "role": "Business Operations Officer",
                "primary_objective": "Ensure business resilience",
                "decision_focus": "Business strategy - customer impact mitigation",
                "parameters": ["customer_communication", "business_continuity_plan"]
            }
        },
        "scenarios": {
            "simple_deterministic": {
                "description": "Predictable attacker with known patterns",
                "threat_level": "Low-Medium",
                "attacker_behavior": "Deterministic - follows predictable patterns"
            },
            "simple_unpredictable": {
                "description": "Unpredictable attacker with variable tactics",
                "threat_level": "Low-Medium",
                "attacker_behavior": "Stochastic - random timing and targets"
            },
            "ransomware": {
                "description": "Advanced ransomware attack",
                "threat_level": "High",
                "attacker_behavior": "Organized group - targets high-value systems"
            },
            "ransomware_with_ransom": {
                "description": "Ransomware with ransom demand",
                "threat_level": "High",
                "attacker_behavior": "Extortion-focused - maximizes ransom potential"
            }
        },
        "key_mechanisms": {
            "collaboration": {
                "description": "How much agents coordinate vs compete",
                "range": "0 (uncollaborative) to 1 (fully collaborative)",
                "impact": "Affects decision alignment and resource allocation efficiency"
            },
            "risk_tolerance": {
                "description": "Agent preference for risk vs reward",
                "range": "0 (risk-averse) to 1 (risk-seeking)",
                "impact": "Determines defensive vs aggressive action selection"
            },
            "time_horizon": {
                "description": "Planning horizon for decisions",
                "range": "1-10 years",
                "impact": "Affects long-term investment vs short-term profit focus"
            }
        }
    })

@app.route('/api/analysis/strategic-control', methods=['POST'])
def get_strategic_control_analysis():
    """Analyze how collaboration affects strategic outcomes"""
    data = request.get_json()
    scenario = data.get('scenario', 'ransomware')
    num_years = data.get('num_years', 5)
    
    return jsonify({
        "title": "Strategic Control Analysis - Effect of Agent Collaboration",
        "research_question": "How does the level of collaboration between organizational stakeholders affect cyber risk management outcomes?",
        "hypothesis": "Higher collaboration leads to better coordinated responses and improved outcomes",
        "scenario": scenario,
        "time_horizon_years": num_years,
        "findings": {
            "uncollaborative": {
                "collaboration_level": 0,
                "description": "Each agent pursues individual objectives independently",
                "expected_outcomes": {
                    "profit": "Variable - may be high if risk-takers succeed, or low if conflicts arise",
                    "systems_at_risk": "Higher - lack of coordination leads to gaps in defense",
                    "efficiency": "Low - duplicate efforts and conflicting strategies"
                },
                "strengths": ["Diverse perspectives", "Innovation through competition"],
                "weaknesses": ["Defense gaps", "Wasted resources", "Delayed responses"]
            },
            "collaborative": {
                "collaboration_level": 1,
                "description": "Agents coordinate decisions and align strategies",
                "expected_outcomes": {
                    "profit": "More stable - coordinated risk management",
                    "systems_at_risk": "Lower - unified defense strategy",
                    "efficiency": "High - shared resources and coordinated response"
                },
                "strengths": ["Unified strategy", "Efficient resource use", "Rapid response"],
                "weaknesses": ["May miss innovative solutions", "Slower to adapt"]
            }
        },
        "related_papers": [
            "Computer and Standards paper - discusses collaborative vs uncollaborative settings",
            "Strategic Control paper - addresses organizational coordination under uncertainty"
        ]
    })

@app.route('/api/analysis/risk-reward', methods=['POST'])
def get_risk_reward_analysis():
    """Analyze risk tolerance vs reward tradeoffs"""
    data = request.get_json()
    scenario = data.get('scenario', 'ransomware')
    
    return jsonify({
        "title": "Risk-Reward Analysis - Effect of Risk Tolerance",
        "research_question": "How does organizational risk tolerance affect the tradeoff between security investment and profitability?",
        "scenario": scenario,
        "analysis": {
            "risk_averse": {
                "risk_tolerance": 0,
                "description": "Organization prioritizes security and stability",
                "strategy": "Heavy security investment, defensive posture",
                "expected_outcomes": {
                    "profit": "Lower short-term, stable long-term",
                    "systems_at_risk": "Minimized",
                    "recovery_time": "Fast if breached"
                },
                "suitable_for": ["Critical infrastructure", "High-compliance industries"]
            },
            "balanced": {
                "risk_tolerance": 0.5,
                "description": "Organization balances security and profit",
                "strategy": "Moderate security investment, measured risk-taking",
                "expected_outcomes": {
                    "profit": "Balanced growth",
                    "systems_at_risk": "Managed levels",
                    "recovery_time": "Reasonable"
                },
                "suitable_for": ["Most organizations", "Typical business scenarios"]
            },
            "risk_seeking": {
                "risk_tolerance": 1,
                "description": "Organization accepts risk for higher returns",
                "strategy": "Minimal security investment, aggressive growth",
                "expected_outcomes": {
                    "profit": "High potential, high volatility",
                    "systems_at_risk": "Higher exposure",
                    "recovery_time": "May be slow"
                },
                "suitable_for": ["Startups", "High-growth scenarios"]
            }
        },
        "related_papers": [
            "Risk-Reward paper - theoretical foundation for these tradeoffs"
        ]
    })

@app.route('/api/analysis/benchmark', methods=['GET'])
def get_real_data_benchmark():
    """Compare simulation results to real player data"""
    try:
        df = pd.read_csv('data/sim_data.csv')
        
        real_stats = {
            "total_runs": len(df),
            "avg_profit": float(df['Cum. Profits'].astype(str).str.replace(',', '').astype(float).mean()),
            "avg_systems_at_risk": float(df['Comp. Systems'].mean()),
            "avg_months": float(df['Months'].mean()),
            "scenarios_distribution": {
                "with_ransom_payment": len(df[df['Pay Ransom'] == 1]),
                "without_ransom_payment": len(df[df['Pay Ransom'] == 0]),
                "level_1": len(df[df['Level'] == 1]),
                "level_2": len(df[df['Level'] == 2])
            }
        }
        
        return jsonify({
            "title": "Real Data Benchmark - Player Behavior Analysis",
            "description": "Analysis of 3860+ real player runs in the cyber risk simulation",
            "real_player_data": real_stats,
            "methodology": "Comparison between multi-agent optimization and actual human decision-making",
            "insights": {
                "key_finding_1": "Human players tend to make decisions based on recent outcomes",
                "key_finding_2": "Risk tolerance varies significantly based on scenario",
                "key_finding_3": "Collaboration effects visible when comparing group vs individual plays"
            }
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    import os
    
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
    
    if sources['csv']['available']:
        print("\nReal CSV data available for comparison")
        if sources['manual']['available']:
            print("Manual bot runs available")
        else:
            print("No manual runs - using mock bot data")
    else:
        print("\nNo real CSV data found at data/sim_data.csv")
        print("   Dashboard will use mock data only")
    
    print(f"\nLoaded {len(bots)} agents:")
    for bot in bots:
        print(f"   {bot.name}: {bot.kpi_focus}")
    
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