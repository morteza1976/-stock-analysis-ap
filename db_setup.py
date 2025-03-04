"""
Database setup script for Stock Analysis & Prediction Platform.
This script creates the database and tables.
"""
import os
import logging
from sqlalchemy import create_engine
from models import Base
import config

# Configure logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(config.LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def create_tables():
    """Create database tables based on the ORM models."""
    try:
        # Ensure the data directory exists
        data_dir = os.path.join(config.BASE_DIR, 'data')
        os.makedirs(data_dir, exist_ok=True)
        
        # Ensure the logs directory exists
        log_dir = os.path.join(config.BASE_DIR, 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        # Create the engine
        engine = create_engine(config.SQLALCHEMY_DATABASE_URI)
        
        # Create tables
        logger.info(f"Creating database tables in {config.SQLALCHEMY_DATABASE_URI}")
        Base.metadata.create_all(engine)
        logger.info("Database tables created successfully")
        
        return True
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        return False

if __name__ == '__main__':
    create_tables() 