"""
MongoDB Integration Module
Handles threshold management and real-time comparison during simulations
"""

import os
from datetime import datetime
from typing import Dict, List, Optional, Any
import logging
from bson.objectid import ObjectId

logger = logging.getLogger(__name__)

_db = None


def init_mongodb():
    """Initialize MongoDB connection."""
    global _db
    if _db is None:
        try:
            from pymongo import MongoClient
            
            mongo_uri = os.getenv(
                "MONGODB",
                "mongodb://localhost:27017"
            )
            db_name = os.getenv("MONGODB_DB", "agentic_research")
            
            client = MongoClient(mongo_uri)
            _db = client[db_name]
            
            _db.command("ping")
            logger.info(f"MongoDB connected: {db_name}")
            
            _ensure_collections()
            
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            _db = None
    
    return _db


def _ensure_collections():
    """Create necessary collections and indexes."""
    if _db is None:
        return
    
    if "thresholds" not in _db.list_collection_names():
        _db.create_collection("thresholds")
        _db.thresholds.create_index("agent_name")
        _db.thresholds.create_index("created_at")
    
    if "simulation_runs" not in _db.list_collection_names():
        _db.create_collection("simulation_runs")
        _db.simulation_runs.create_index("simulation_id")
        _db.simulation_runs.create_index("timestamp")
        _db.simulation_runs.create_index("threshold_id")
    
    if "comparisons" not in _db.list_collection_names():
        _db.create_collection("comparisons")
        _db.comparisons.create_index("simulation_id")
        _db.comparisons.create_index("timestamp")


class ThresholdManager:
    """Manages agent thresholds in MongoDB."""
    
    @staticmethod
    def create_threshold(
        agent_name: str,
        kpi_name: str,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None,
        target_value: Optional[float] = None,
        description: str = ""
    ) -> Optional[str]:
        """
        Create a new threshold for an agent KPI.
        
        Args:
            agent_name: Name of the agent (CFO, CRO, COO, etc.)
            kpi_name: Name of the KPI
            min_value: Minimum acceptable value
            max_value: Maximum acceptable value
            target_value: Target value
            description: Description of the threshold
        
        Returns:
            ObjectId of created threshold as string, or None on error
        """
        db = init_mongodb()
        if db is None:
            logger.warning("MongoDB not available, threshold not saved")
            return None
        
        try:
            threshold_doc = {
                "agent_name": agent_name,
                "kpi_name": kpi_name,
                "min_value": min_value,
                "max_value": max_value,
                "target_value": target_value,
                "description": description,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "is_active": True
            }
            
            result = db.thresholds.insert_one(threshold_doc)
            logger.info(f"✓ Threshold created: {agent_name} - {kpi_name}")
            return str(result.inserted_id)
        
        except Exception as e:
            logger.error(f"Error creating threshold: {e}")
            return None
    
    @staticmethod
    def get_threshold(threshold_id: str) -> Optional[Dict]:
        """Get a specific threshold by ID."""
        db = init_mongodb()
        if db is None:
            return None
        
        try:
            threshold = db.thresholds.find_one({"_id": ObjectId(threshold_id)})
            if threshold:
                threshold["_id"] = str(threshold["_id"])
            return threshold
        except Exception as e:
            logger.error(f"Error fetching threshold: {e}")
            return None
    
    @staticmethod
    def get_agent_thresholds(agent_name: str) -> List[Dict]:
        """Get all active thresholds for an agent."""
        db = init_mongodb()
        if db is None:
            return []
        
        try:
            thresholds = list(db.thresholds.find({
                "agent_name": agent_name,
                "is_active": True
            }))
            
            for t in thresholds:
                t["_id"] = str(t["_id"])
            
            return thresholds
        except Exception as e:
            logger.error(f"Error fetching agent thresholds: {e}")
            return []
    
    @staticmethod
    def update_threshold(
        threshold_id: str,
        **updates
    ) -> bool:
        """Update a threshold."""
        db = init_mongodb()
        if db is None:
            return False
        
        try:
            updates["updated_at"] = datetime.utcnow()
            result = db.thresholds.update_one(
                {"_id": ObjectId(threshold_id)},
                {"$set": updates}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error updating threshold: {e}")
            return False
    
    @staticmethod
    def delete_threshold(threshold_id: str) -> bool:
        """Soft delete a threshold (mark as inactive)."""
        db = init_mongodb()
        if db is None:
            return False
        
        try:
            result = db.thresholds.update_one(
                {"_id": ObjectId(threshold_id)},
                {"$set": {"is_active": False, "updated_at": datetime.utcnow()}}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error deleting threshold: {e}")
            return False
    
    @staticmethod
    def get_all_thresholds() -> List[Dict]:
        """Get all active thresholds."""
        db = init_mongodb()
        if db is None:
            return []
        
        try:
            thresholds = list(db.thresholds.find({"is_active": True}))
            for t in thresholds:
                t["_id"] = str(t["_id"])
            return thresholds
        except Exception as e:
            logger.error(f"Error fetching all thresholds: {e}")
            return []


class SimulationComparator:
    """Compares simulation runs against thresholds."""
    
    @staticmethod
    def log_simulation_run(
        simulation_id: str,
        threshold_id: str,
        agent_name: str,
        kpi_name: str,
        actual_value: float,
        target_value: Optional[float] = None,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None,
        metadata: Optional[Dict] = None
    ) -> Optional[str]:
        """
        Log a simulation run against a threshold.
        
        Args:
            simulation_id: Unique identifier for the simulation
            threshold_id: ID of the threshold being compared
            agent_name: Name of the agent
            kpi_name: Name of the KPI
            actual_value: The actual value from simulation
            target_value: Optional target value
            min_value: Optional minimum acceptable value
            max_value: Optional maximum acceptable value
            metadata: Additional metadata about the run
        
        Returns:
            ObjectId of logged run as string, or None on error
        """
        db = init_mongodb()
        if db is None:
            logger.warning("MongoDB not available, simulation run not logged")
            return None
        
        try:
            status = "on_target"
            if min_value is not None and actual_value < min_value:
                status = "below_min"
            elif max_value is not None and actual_value > max_value:
                status = "above_max"
            elif target_value is not None:
                tolerance = abs(target_value) * 0.1
                if not (target_value - tolerance <= actual_value <= target_value + tolerance):
                    status = "off_target"
            
            run_doc = {
                "simulation_id": simulation_id,
                "threshold_id": threshold_id,
                "agent_name": agent_name,
                "kpi_name": kpi_name,
                "actual_value": actual_value,
                "target_value": target_value,
                "min_value": min_value,
                "max_value": max_value,
                "status": status,
                "timestamp": datetime.utcnow(),
                "metadata": metadata or {}
            }
            
            result = db.simulation_runs.insert_one(run_doc)
            return str(result.inserted_id)
        
        except Exception as e:
            logger.error(f"Error logging simulation run: {e}")
            return None
    
    @staticmethod
    def get_simulation_results(simulation_id: str) -> Dict:
        """Get all results for a specific simulation."""
        db = init_mongodb()
        if db is None:
            return {}
        
        try:
            runs = list(db.simulation_runs.find({"simulation_id": simulation_id}))
            
            for run in runs:
                run["_id"] = str(run["_id"])
                if "threshold_id" in run:
                    run["threshold_id"] = str(run["threshold_id"])
            
            results_by_agent = {}
            for run in runs:
                agent = run["agent_name"]
                kpi = run["kpi_name"]
                
                if agent not in results_by_agent:
                    results_by_agent[agent] = {}
                if kpi not in results_by_agent[agent]:
                    results_by_agent[agent][kpi] = []
                
                results_by_agent[agent][kpi].append({
                    "actual": run["actual_value"],
                    "target": run["target_value"],
                    "status": run["status"],
                    "timestamp": run["timestamp"].isoformat()
                })
            
            summary = {
                "total_runs": len(runs),
                "passed": len([r for r in runs if r["status"] == "on_target"]),
                "failed": len([r for r in runs if r["status"] != "on_target"]),
                "by_agent": results_by_agent,
                "runs": runs
            }
            
            return summary
        
        except Exception as e:
            logger.error(f"Error fetching simulation results: {e}")
            return {}
    
    @staticmethod
    def log_comparison(
        simulation_id: str,
        threshold_id: str,
        is_within_threshold: bool,
        actual_value: float,
        threshold_min: Optional[float] = None,
        threshold_max: Optional[float] = None,
        notes: str = ""
    ) -> Optional[str]:
        """Log a comparison result."""
        db = init_mongodb()
        if db is None:
            return None
        
        try:
            comparison_doc = {
                "simulation_id": simulation_id,
                "threshold_id": threshold_id,
                "is_within_threshold": is_within_threshold,
                "actual_value": actual_value,
                "threshold_min": threshold_min,
                "threshold_max": threshold_max,
                "notes": notes,
                "timestamp": datetime.utcnow()
            }
            
            result = db.comparisons.insert_one(comparison_doc)
            return str(result.inserted_id)
        
        except Exception as e:
            logger.error(f"Error logging comparison: {e}")
            return None
    
    @staticmethod
    def get_comparison_history(threshold_id: str, limit: int = 100) -> List[Dict]:
        """Get comparison history for a threshold."""
        db = init_mongodb()
        if db is None:
            return []
        
        try:
            comparisons = list(db.comparisons.find(
                {"threshold_id": threshold_id}
            ).sort("timestamp", -1).limit(limit))
            
            for comp in comparisons:
                comp["_id"] = str(comp["_id"])
                comp["threshold_id"] = str(comp["threshold_id"])
            
            return comparisons
        
        except Exception as e:
            logger.error(f"Error fetching comparison history: {e}")
            return []
    
    @staticmethod
    def get_statistics(
        threshold_id: Optional[str] = None,
        agent_name: Optional[str] = None,
        days: int = 30
    ) -> Dict:
        """Get statistics on threshold compliance."""
        db = init_mongodb()
        if db is None:
            return {}
        
        try:
            runs = list(db.simulation_runs.find())
            
            if not runs:
                return {"total": 0, "passed": 0, "failed": 0, "pass_rate": 0}
            
            total = len(runs)
            passed = len([r for r in runs if r["status"] == "on_target"])
            failed = total - passed
            
            return {
                "total": total,
                "passed": passed,
                "failed": failed,
                "pass_rate": round((passed / total) * 100, 2),
                "days": days,
                "agent": agent_name,
                "threshold": threshold_id
            }
        
        except Exception as e:
            logger.error(f"Error calculating statistics: {e}")
            return {}
