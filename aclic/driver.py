from fastapi_app import app
import uvicorn
import logging
from datetime import datetime
import os

# Set console encoding to UTF-8 to handle special characters
os.environ["PYTHONIOENCODING"] = "utf-8"

# Ensure logs directory exists
logs_dir = "logs"
os.makedirs(logs_dir, exist_ok=True)

# Configure logging with unique log file per run
log_filename = os.path.join(logs_dir, f"log_driver_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_filename, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    try:
        logger.info("Starting FastAPI server...")
        uvicorn.run(app, port=8000)
    except Exception as e:
        logger.error(f"Failed to start server: {str(e)}")
        raise