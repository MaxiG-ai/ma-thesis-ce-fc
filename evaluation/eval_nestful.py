import logging
import asyncio
from nestful_adapter import NestfulAdapter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)
    

if __name__ == "__main__":
    
    nestful_b = NestfulAdapter("config.toml")

    logger.info("Configuration:")
    for key, value in nestful_b.cfg.items():
        logger.info(f"{key}: {value}")

    # run the async benchmark and await its result
    asyncio.run(nestful_b.run_benchmark())