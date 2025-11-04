"""
SQLite-based storage for evaluation results.
"""

import sqlite3
import json
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from datetime import datetime

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class ResultsStorage:
    """SQLite-based storage for evaluation results with JSON export capabilities."""
    
    def __init__(self, results_dir: str = "results"):
        """
        Initialize ResultsStorage with SQLite database.
        
        Args:
            results_dir: Directory to store the SQLite database file
        """
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
        self.db_path = self.results_dir / "evaluation_results.db"
        self._initialize_database()
    
    def _initialize_database(self) -> None:
        """Initialize SQLite database with required tables."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create evaluation_runs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS evaluation_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                model_name TEXT NOT NULL,
                model_provider TEXT NOT NULL,
                memory_method TEXT NOT NULL,
                benchmark TEXT NOT NULL,
                status TEXT NOT NULL,
                duration_seconds REAL,
                results_json TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create evaluation_results table for detailed results storage
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS evaluation_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id INTEGER NOT NULL,
                key TEXT NOT NULL,
                value TEXT,
                FOREIGN KEY (run_id) REFERENCES evaluation_runs (id)
            )
        """)
        
        # Create indexes for common queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_model_name 
            ON evaluation_runs (model_name)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_memory_method 
            ON evaluation_runs (memory_method)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_benchmark 
            ON evaluation_runs (benchmark)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_status 
            ON evaluation_runs (status)
        """)
        
        conn.commit()
        conn.close()
    
    def save_result(self, result: Dict[str, Any]) -> int:
        """
        Save evaluation result to SQLite database.
        
        Args:
            result: Dictionary containing evaluation result data
            
        Returns:
            ID of the saved result
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Extract model information
            model_info = result.get("model", {})
            model_name = model_info.get("name") if isinstance(model_info, dict) else str(model_info)
            model_provider = model_info.get("provider", "unknown") if isinstance(model_info, dict) else "unknown"
            
            # Prepare data
            timestamp = result.get("timestamp", datetime.now().isoformat())
            memory_method = result.get("memory_method", "unknown")
            benchmark = result.get("benchmark", "unknown")
            status = result.get("status", "unknown")
            duration_seconds = result.get("duration_seconds")
            results_json = json.dumps(result.get("results", {}))
            
            # Insert into evaluation_runs
            cursor.execute("""
                INSERT INTO evaluation_runs 
                (timestamp, model_name, model_provider, memory_method, 
                 benchmark, status, duration_seconds, results_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (timestamp, model_name, model_provider, memory_method,
                  benchmark, status, duration_seconds, results_json))
            
            run_id = cursor.lastrowid
            
            conn.commit()
            return run_id
            
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def get_result(self, result_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve evaluation result by ID.
        
        Args:
            result_id: ID of the result to retrieve
            
        Returns:
            Dictionary containing result data or None if not found
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT id, timestamp, model_name, model_provider, memory_method,
                       benchmark, status, duration_seconds, results_json, created_at
                FROM evaluation_runs 
                WHERE id = ?
            """, (result_id,))
            
            row = cursor.fetchone()
            if not row:
                return None
            
            result = {
                "id": row[0],
                "timestamp": row[1],
                "model_name": row[2],
                "model_provider": row[3],
                "memory_method": row[4],
                "benchmark": row[5],
                "status": row[6],
                "duration_seconds": row[7],
                "results": json.loads(row[8]) if row[8] else {},
                "created_at": row[9]
            }
            
            return result
            
        finally:
            conn.close()
    
    def query_results(
        self, 
        model_name: Optional[str] = None,
        model_provider: Optional[str] = None,
        memory_method: Optional[str] = None,
        benchmark: Optional[str] = None,
        status: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Query evaluation results with optional filters.
        
        Args:
            model_name: Filter by model name
            model_provider: Filter by model provider
            memory_method: Filter by memory method
            benchmark: Filter by benchmark
            status: Filter by status
            limit: Maximum number of results to return
            
        Returns:
            List of matching results
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Build query
            query = """
                SELECT id, timestamp, model_name, model_provider, memory_method,
                       benchmark, status, duration_seconds, results_json, created_at
                FROM evaluation_runs 
                WHERE 1=1
            """
            params = []
            
            if model_name:
                query += " AND model_name = ?"
                params.append(model_name)
            
            if model_provider:
                query += " AND model_provider = ?"
                params.append(model_provider)
            
            if memory_method:
                query += " AND memory_method = ?"
                params.append(memory_method)
            
            if benchmark:
                query += " AND benchmark = ?"
                params.append(benchmark)
            
            if status:
                query += " AND status = ?"
                params.append(status)
            
            query += " ORDER BY created_at DESC"
            
            if limit:
                query += " LIMIT ?"
                params.append(limit)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            results = []
            for row in rows:
                result = {
                    "id": row[0],
                    "timestamp": row[1],
                    "model_name": row[2],
                    "model_provider": row[3],
                    "memory_method": row[4],
                    "benchmark": row[5],
                    "status": row[6],
                    "duration_seconds": row[7],
                    "results": json.loads(row[8]) if row[8] else {},
                    "created_at": row[9]
                }
                results.append(result)
            
            return results
            
        finally:
            conn.close()
    
    def export_to_json(self, filepath: str, **filters) -> None:
        """
        Export results to JSON file.
        
        Args:
            filepath: Path to save JSON file
            **filters: Query filters (same as query_results)
        """
        results = self.query_results(**filters)
        
        with open(filepath, 'w') as f:
            json.dump(results, f, indent=2, default=str)
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get summary statistics of all stored results.
        
        Returns:
            Dictionary containing summary statistics
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Total counts
            cursor.execute("SELECT COUNT(*) FROM evaluation_runs")
            total_runs = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM evaluation_runs WHERE status = 'success'")
            successful_runs = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM evaluation_runs WHERE status = 'error'")
            failed_runs = cursor.fetchone()[0]
            
            # Success rate
            success_rate = successful_runs / total_runs if total_runs > 0 else 0
            
            # Unique values
            cursor.execute("SELECT DISTINCT model_name FROM evaluation_runs")
            models = [row[0] for row in cursor.fetchall()]
            
            cursor.execute("SELECT DISTINCT memory_method FROM evaluation_runs")
            memory_methods = [row[0] for row in cursor.fetchall()]
            
            cursor.execute("SELECT DISTINCT benchmark FROM evaluation_runs")
            benchmarks = [row[0] for row in cursor.fetchall()]
            
            return {
                "total_runs": total_runs,
                "successful_runs": successful_runs,
                "failed_runs": failed_runs,
                "success_rate": success_rate,
                "models": models,
                "memory_methods": memory_methods,
                "benchmarks": benchmarks,
                "database_path": str(self.db_path)
            }
            
        finally:
            conn.close()
    
    def delete_result(self, result_id: int) -> bool:
        """
        Delete a result by ID.
        
        Args:
            result_id: ID of the result to delete
            
        Returns:
            True if deleted, False if not found
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("DELETE FROM evaluation_runs WHERE id = ?", (result_id,))
            deleted = cursor.rowcount > 0
            conn.commit()
            return deleted
            
        finally:
            conn.close()
    
    def clear_all_results(self) -> None:
        """Clear all stored results."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("DELETE FROM evaluation_results")
            cursor.execute("DELETE FROM evaluation_runs")
            conn.commit()
            
        finally:
            conn.close()