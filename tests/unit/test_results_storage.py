"""

Tests for the SQLite-based ResultsStorage class.
"""

import sys
import tempfile
import json
import sqlite3
from pathlib import Path
from datetime import datetime

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def test_results_storage_initialization():
    """Test ResultsStorage initialization with SQLite database."""
    from evaluation.results import ResultsStorage
    
    with tempfile.TemporaryDirectory() as temp_dir:
        storage = ResultsStorage(results_dir=temp_dir)
        
        # Should create database file
        db_path = Path(temp_dir) / "evaluation_results.db"
        assert db_path.exists()
        
        # Should have proper tables
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        assert "evaluation_runs" in tables
        assert "evaluation_results" in tables
        
        conn.close()


def test_results_storage_save_result():
    """Test saving evaluation results to SQLite."""
    from evaluation.results import ResultsStorage
    
    with tempfile.TemporaryDirectory() as temp_dir:
        storage = ResultsStorage(results_dir=temp_dir)
        
        # Test result data
        result = {
            "timestamp": "2025-11-04T10:00:00",
            "duration_seconds": 120.5,
            "model": {"name": "llama3.2:3b", "provider": "ollama"},
            "memory_method": "truncation",
            "benchmark": "nestful",
            "results": {
                "score": 0.85,
                "total_tasks": 10,
                "successful_tasks": 8
            },
            "status": "success"
        }
        
        result_id = storage.save_result(result)
        
        assert isinstance(result_id, int)
        assert result_id > 0


def test_results_storage_get_result():
    """Test retrieving evaluation results from SQLite."""
    from evaluation.results import ResultsStorage
    
    with tempfile.TemporaryDirectory() as temp_dir:
        storage = ResultsStorage(results_dir=temp_dir)
        
        # Save a result first
        original_result = {
            "timestamp": "2025-11-04T10:00:00",
            "duration_seconds": 120.5,
            "model": {"name": "llama3.2:3b", "provider": "ollama"},
            "memory_method": "truncation",
            "benchmark": "nestful",
            "results": {"score": 0.85},
            "status": "success"
        }
        
        result_id = storage.save_result(original_result)
        
        # Retrieve the result
        retrieved_result = storage.get_result(result_id)
        
        assert retrieved_result is not None
        assert retrieved_result["id"] == result_id
        assert retrieved_result["model_name"] == "llama3.2:3b"
        assert retrieved_result["model_provider"] == "ollama"
        assert retrieved_result["memory_method"] == "truncation"
        assert retrieved_result["benchmark"] == "nestful"
        assert retrieved_result["status"] == "success"
        assert retrieved_result["duration_seconds"] == 120.5


def test_results_storage_query_results():
    """Test querying evaluation results with filters."""
    from evaluation.results import ResultsStorage
    
    with tempfile.TemporaryDirectory() as temp_dir:
        storage = ResultsStorage(results_dir=temp_dir)
        
        # Save multiple results
        results = [
            {
                "timestamp": "2025-11-04T10:00:00",
                "model": {"name": "llama3.2:3b", "provider": "ollama"},
                "memory_method": "truncation",
                "benchmark": "nestful",
                "results": {"score": 0.85},
                "status": "success"
            },
            {
                "timestamp": "2025-11-04T11:00:00",
                "model": {"name": "llama3.1:8b", "provider": "ollama"},
                "memory_method": "truncation",
                "benchmark": "nestful",
                "results": {"score": 0.90},
                "status": "success"
            },
            {
                "timestamp": "2025-11-04T12:00:00",
                "model": {"name": "llama3.2:3b", "provider": "ollama"},
                "memory_method": "sliding_window",
                "benchmark": "mcpbench",
                "results": {"score": 0.75},
                "status": "success"
            }
        ]
        
        for result in results:
            storage.save_result(result)
        
        # Query by model
        llama_32_results = storage.query_results(model_name="llama3.2:3b")
        assert len(llama_32_results) == 2
        
        # Query by memory method
        truncation_results = storage.query_results(memory_method="truncation")
        assert len(truncation_results) == 2
        
        # Query by benchmark
        nestful_results = storage.query_results(benchmark="nestful")
        assert len(nestful_results) == 2
        
        # Combined query
        specific_results = storage.query_results(
            model_name="llama3.2:3b", 
            memory_method="truncation"
        )
        assert len(specific_results) == 1


def test_results_storage_export_json():
    """Test exporting results to JSON format."""
    from evaluation.results import ResultsStorage
    
    with tempfile.TemporaryDirectory() as temp_dir:
        storage = ResultsStorage(results_dir=temp_dir)
        
        # Save some results
        result = {
            "timestamp": "2025-11-04T10:00:00",
            "model": {"name": "llama3.2:3b", "provider": "ollama"},
            "memory_method": "truncation",
            "benchmark": "nestful",
            "results": {"score": 0.85, "details": "test"},
            "status": "success"
        }
        
        storage.save_result(result)
        
        # Export to JSON
        json_path = Path(temp_dir) / "export.json"
        storage.export_to_json(str(json_path))
        
        assert json_path.exists()
        
        # Verify JSON content
        with open(json_path, 'r') as f:
            exported_data = json.load(f)
        
        assert isinstance(exported_data, list)
        assert len(exported_data) == 1
        assert exported_data[0]["model_name"] == "llama3.2:3b"
        assert exported_data[0]["benchmark"] == "nestful"


def test_results_storage_get_summary():
    """Test getting summary statistics from stored results."""
    from evaluation.results import ResultsStorage
    
    with tempfile.TemporaryDirectory() as temp_dir:
        storage = ResultsStorage(results_dir=temp_dir)
        
        # Save results with different statuses
        results = [
            {
                "timestamp": "2025-11-04T10:00:00",
                "model": {"name": "llama3.2:3b", "provider": "ollama"},
                "memory_method": "truncation",
                "benchmark": "nestful",
                "results": {"score": 0.85},
                "status": "success"
            },
            {
                "timestamp": "2025-11-04T11:00:00",
                "model": {"name": "llama3.1:8b", "provider": "ollama"},
                "memory_method": "truncation",
                "benchmark": "nestful",
                "results": {"score": 0.90},
                "status": "success"
            },
            {
                "timestamp": "2025-11-04T12:00:00",
                "model": {"name": "unknown", "provider": "ollama"},
                "memory_method": "truncation",
                "benchmark": "nestful",
                "results": {},
                "status": "error"
            }
        ]
        
        for result in results:
            storage.save_result(result)
        
        summary = storage.get_summary()
        
        assert summary["total_runs"] == 3
        assert summary["successful_runs"] == 2
        assert summary["failed_runs"] == 1
        assert summary["success_rate"] == 2/3
        assert "models" in summary
        assert "memory_methods" in summary
        assert "benchmarks" in summary


def test_results_storage_delete_results():
    """Test deleting results from SQLite."""
    from evaluation.results import ResultsStorage
    
    with tempfile.TemporaryDirectory() as temp_dir:
        storage = ResultsStorage(results_dir=temp_dir)
        
        # Save a result
        result = {
            "timestamp": "2025-11-04T10:00:00",
            "model": {"name": "llama3.2:3b", "provider": "ollama"},
            "memory_method": "truncation",
            "benchmark": "nestful",
            "results": {"score": 0.85},
            "status": "success"
        }
        
        result_id = storage.save_result(result)
        
        # Verify it exists
        assert storage.get_result(result_id) is not None
        
        # Delete it
        deleted = storage.delete_result(result_id)
        assert deleted is True
        
        # Verify it's gone
        assert storage.get_result(result_id) is None


def test_results_storage_database_schema():
    """Test that the database schema is created correctly."""
    from evaluation.results import ResultsStorage
    
    with tempfile.TemporaryDirectory() as temp_dir:
        storage = ResultsStorage(results_dir=temp_dir)
        
        db_path = Path(temp_dir) / "evaluation_results.db"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check evaluation_runs table structure
        cursor.execute("PRAGMA table_info(evaluation_runs)")
        columns = [row[1] for row in cursor.fetchall()]
        
        expected_columns = [
            "id", "timestamp", "model_name", "model_provider", 
            "memory_method", "benchmark", "status", "duration_seconds",
            "results_json", "created_at"
        ]
        
        for col in expected_columns:
            assert col in columns
        
        conn.close()


def test_results_storage_concurrent_access():
    """Test that multiple ResultsStorage instances can access the same database."""
    from evaluation.results import ResultsStorage
    
    with tempfile.TemporaryDirectory() as temp_dir:
        storage1 = ResultsStorage(results_dir=temp_dir)
        storage2 = ResultsStorage(results_dir=temp_dir)
        
        # Save with first instance
        result = {
            "timestamp": "2025-11-04T10:00:00",
            "model": {"name": "llama3.2:3b", "provider": "ollama"},
            "memory_method": "truncation",
            "benchmark": "nestful",
            "results": {"score": 0.85},
            "status": "success"
        }
        
        result_id = storage1.save_result(result)
        
        # Read with second instance
        retrieved = storage2.get_result(result_id)
        
        assert retrieved is not None
        assert retrieved["id"] == result_id