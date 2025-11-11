#!/usr/bin/env python3
"""
Multi-Component Evaluation Script

This script runs comprehensive evaluations across multiple models, memory methods, 
and benchmarks using the EvaluationOrchestrator.

Usage:
    uv run python evaluation/run_evaluation.py
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

import toml

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from evaluation.orchestrator import EvaluationOrchestrator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_config(config_path: str) -> dict:
    """Load configuration from TOML file."""
    try:
        with open(config_path, 'r') as f:
            return toml.load(f)
    except FileNotFoundError:
        logger.error(f"Configuration file not found: {config_path}")
        raise
    except toml.TomlDecodeError as e:
        logger.error(f"Error parsing TOML configuration: {e}")
        raise


def validate_config(config: dict) -> None:
    """Validate that the configuration has required fields for multi-component evaluation."""
    required_fields = ["memory_methods", "executed_benchmarks", "providers"]
    missing_fields = [field for field in required_fields if field not in config]
    
    if missing_fields:
        raise ValueError(f"Configuration missing required fields: {missing_fields}")
    
    # Validate that arrays are not empty
    for field in ["memory_methods", "executed_benchmarks"]:
        if field in config and not config[field]:
            raise ValueError(f"Configuration field '{field}' cannot be empty")
    
    # Validate providers configuration
    providers = config.get("providers", {})
    if not providers:
        raise ValueError("No providers configured")
    
    # Check that at least one provider has enabled models
    has_enabled_models = False
    for provider_name, provider_config in providers.items():
        if provider_config.get("enabled_models"):
            has_enabled_models = True
            break
    
    if not has_enabled_models:
        raise ValueError("No models enabled in any provider. Set enabled_models for at least one provider.")
    
    logger.info("Configuration validation passed")


async def run_evaluation(config: dict) -> int:
    """Run multi-component evaluation using the orchestrator."""
    logger.info("Starting multi-component evaluation...")
    
    try:
        # Initialize orchestrator
        orchestrator = EvaluationOrchestrator(config)
        
        # Run full evaluation
        summary = await orchestrator.run_full_evaluation()
        
        logger.info("Multi-component evaluation completed successfully!")
        logger.info(f"Total evaluation runs: {summary['total_runs']}")
        logger.info(f"Successful runs: {summary['successful_runs']}")
        logger.info(f"Failed runs: {summary['failed_runs']}")
        logger.info(f"Success rate: {summary['success_rate']:.2%}")
        
        # Display tested components
        logger.info(f"Models tested: {summary.get('models_tested', [])}")
        logger.info(f"Memory methods tested: {summary.get('memory_methods_tested', [])}")
        logger.info(f"Benchmarks tested: {summary.get('benchmarks_tested', [])}")
        
        # Show preview of individual results
        results = summary.get('results', [])
        for i, result in enumerate(results[:3]):
            logger.info(f"Result {i+1}: {result['model']['name']} + {result['memory_method']} + {result['benchmark']}")
            logger.info(f"  Status: {result['status']}")
            if result['status'] == 'success':
                benchmark_results = result.get('results', {})
                score = benchmark_results.get('score', 'N/A')
                logger.info(f"  Score: {score}")
            else:
                logger.info(f"  Error: {result.get('error', 'Unknown error')}")
        
        if len(results) > 3:
            logger.info(f"... and {len(results) - 3} more results")
        
        # Return appropriate exit code
        return 0 if summary['failed_runs'] == 0 else 1
        
    except Exception as e:
        logger.error(f"Multi-component evaluation failed: {e}")
        logger.exception("Full error details:")
        return 1


async def main():
    """Main evaluation function."""
    logger.info("Starting evaluation script...")
    
    try:
        # Load configuration
        config_path = os.path.join(project_root, "evaluation", "config.toml")
        config = load_config(config_path)
        
        logger.info("Configuration loaded successfully")
        
        # Validate configuration
        validate_config(config)
        
        # Display configuration summary
        providers = config.get("providers", {})
        total_enabled_models = sum(
            len(provider_config.get("enabled_models", []))
            for provider_config in providers.values()
        )
        logger.info(f"Enabled models: {total_enabled_models} across {len(providers)} providers")
        logger.info(f"Memory methods: {config['memory_methods']}")
        logger.info(f"Benchmarks: {config['executed_benchmarks']}")
        
        total_combinations = (
            total_enabled_models * 
            len(config['memory_methods']) * 
            len(config['executed_benchmarks'])
        )
        logger.info(f"Total combinations to evaluate: {total_combinations}")
        
        # Run evaluation
        return await run_evaluation(config)
        
    except Exception as e:
        logger.error(f"Evaluation failed: {e}")
        logger.exception("Full error details:")
        return 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("Evaluation interrupted by user.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)
