#!/usr/bin/env python3
"""
MCP Bench Evaluation Script.

This script runs the MCP Benchmark using configuration from config.toml,
providing a standardized, config-driven approach to benchmark evaluation.
"""
import sys
import logging
import argparse
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


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="MCP Bench Evaluation (Config-Driven)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                                    # Run with default config.toml settings
  %(prog)s --config my_config.toml            # Use custom config file
  %(prog)s --models llama3.1:8b mistral:7b    # Override models from config
  %(prog)s --task-limit 10                    # Override task limit from config
  %(prog)s --section custom_mcpbench          # Use different TOML section
        """
    )
    
    parser.add_argument(
        "--config",
        default="evaluation/config.toml",
        help="Path to TOML configuration file (default: evaluation/config.toml)"
    )
    
    parser.add_argument(
        "--section",
        default="mcpbench",
        help="Section name in TOML file (default: mcpbench)"
    )
    
    parser.add_argument(
        "--models",
        nargs="*",
        help="Override model(s) from config (space-separated list)"
    )
    
    parser.add_argument(
        "--task-limit",
        type=int,
        help="Override task limit from config"
    )
    
    parser.add_argument(
        "--output",
        help="Override output filename (default: auto-generated timestamp)"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    return parser.parse_args()


async def main():
    """Main entry point for config-driven MCP Bench evaluation."""
    args = parse_arguments()
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        # Load configuration from TOML file
        logger.info(f"Loading configuration from {args.config}, section: {args.section}")
        config = MCPBenchAdapter.load_config_from_file(args.config, args.section)
        
        # Create adapter
        adapter = MCPBenchAdapter(config)
        
        # Log configuration summary
        logger.info("=" * 80)
        logger.info("MCP Bench Configuration Summary")
        logger.info("=" * 80)
        logger.info(f"Model Provider: {adapter.model_provider}")
        logger.info(f"Models: {adapter.get_selected_models()}")
        logger.info(f"Tasks File: {adapter.tasks_file}")
        logger.info(f"Task Limit: {adapter.task_limit if adapter.task_limit else 'all tasks'}")
        logger.info(f"Temperature: {adapter.temperature}")
        logger.info(f"Max Tokens: {adapter.max_tokens}")
        logger.info(f"Distraction Servers: {adapter.enable_distraction_servers} (count: {adapter.distraction_count})")
        logger.info(f"Judge Stability: {adapter.enable_judge_stability}")
        logger.info(f"Filter Problematic Tools: {adapter.filter_problematic_tools}")
        logger.info(f"Output Directory: {adapter.save_directory}")
        logger.info("=" * 80)
        
        # Override with command-line arguments if provided
        selected_models = args.models if args.models else None
        task_limit = args.task_limit if args.task_limit is not None else None
        
        if selected_models:
            logger.info(f"Command-line override - Models: {selected_models}")
        if task_limit is not None:
            logger.info(f"Command-line override - Task Limit: {task_limit}")
        
        # Run benchmark
        logger.info("Starting benchmark execution...")
        results = await adapter.run_benchmark(
            selected_models=selected_models,
            task_limit=task_limit
        )
        
        # Save results
        output_file = await adapter.save_results(
            results,
            filename=args.output
        )
        
        # Log summary
        logger.info("=" * 80)
        logger.info("Benchmark Execution Complete")
        logger.info("=" * 80)
        logger.info(f"Results saved to: {output_file}")
        
        # Print model-level summary
        if "models" in results:
            logger.info("\nModel Results Summary:")
            for model_name, model_results in results["models"].items():
                overall_score = model_results.get("overall_score", "N/A")
                task_count = len(model_results.get("tasks", []))
                logger.info(f"  {model_name}: {overall_score:.3f} ({task_count} tasks)")
        
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