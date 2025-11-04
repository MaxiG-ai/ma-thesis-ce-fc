#!/usr/bin/env python3
"""
MCP Bench Evaluation Script.

This script runs the MCP Benchmark using configuration from config.toml,
providing a standardized, config-driven approach to benchmark evaluation.
"""
import sys
import logging
import asyncio
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

# Import after path is set
from evaluation.mcpbench_adapter import MCPBenchAdapter  # noqa: E402

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def main():
    """Main entry point for config-driven MCP Bench evaluation."""
    
    try:
        # Create adapter (automatically loads config)
        logger.info("Loading configuration from config.toml, section: mcpbench")
        adapter = MCPBenchAdapter()
        
        # Print configuration summary
        adapter.print_config()
        
        # Run benchmark
        logger.info("Starting benchmark execution...")
        results = await adapter.run_benchmark(
            selected_models=adapter.get_selected_models(),
            task_limit=adapter.cfg.get("task_limit")
        )
        
        # Save results
        output_file = await adapter.save_results(
            results,
            filename=adapter.cfg.get("results_dir")
        )
        
        # Log summary
        logger.info("=" * 80)
        logger.info("Benchmark Execution Complete")
        logger.info("=" * 80)
        logger.info(f"Results saved to: {output_file}")

        
        logger.info("\nNote: The overall score is calculated as the average of four main dimensions:")
        logger.info("  - Schema Understanding")
        logger.info("  - Task Completion")
        logger.info("  - Tool Usage")
        logger.info("  - Planning Effectiveness")
        logger.info("=" * 80)
        
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"Configuration file error: {e}")
        return 1
    except ValueError as e:
        logger.error(f"Configuration validation error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Benchmark execution error: {e}")
        import traceback
        logger.debug(f"Full traceback:\n{traceback.format_exc()}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)