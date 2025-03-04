"""
Configuration settings for the Stock Analysis & Prediction Platform
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file (if it exists)
load_dotenv()

# Base directory
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Database Configuration
DATABASE_TYPE = os.environ.get('DATABASE_TYPE', 'sqlite')  # 'sqlite' or 'postgresql'

if DATABASE_TYPE == 'sqlite':
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL', f'sqlite:///{os.path.join(BASE_DIR, "data", "stocks.db")}'
    )
else:
    # PostgreSQL connection
    db_user = os.environ.get('DB_USER', 'postgres')
    db_password = os.environ.get('DB_PASSWORD', 'postgres')
    db_host = os.environ.get('DB_HOST', 'localhost')
    db_port = os.environ.get('DB_PORT', '5432')
    db_name = os.environ.get('DB_NAME', 'stockanalysis')
    SQLALCHEMY_DATABASE_URI = f'postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}'

SQLALCHEMY_TRACK_MODIFICATIONS = False

# API Configuration
# Yahoo Finance API doesn't require an API key as we're using yfinance
# If you add other APIs, store their keys in environment variables
ALPHA_VANTAGE_API_KEY = os.environ.get('ALPHA_VANTAGE_API_KEY', '')
POLYGON_API_KEY = os.environ.get('POLYGON_API_KEY', '')

# Application Configuration
DEBUG = os.environ.get('DEBUG', 'True').lower() in ('true', 't', '1')
SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')
PORT = int(os.environ.get('PORT', 5000))

# Data Collection Configuration
STOCK_COUNT = int(os.environ.get('STOCK_COUNT', 500))  # Number of stocks to analyze
DEFAULT_HISTORY_PERIOD = "2y"  # Default period for historical data

# Scheduler Configuration
UPDATE_INTERVAL_HOURS = int(os.environ.get('UPDATE_INTERVAL_HOURS', 24))
MARKET_HOURS_ONLY = os.environ.get('MARKET_HOURS_ONLY', 'True').lower() in ('true', 't', '1')

# Cache Configuration
REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
CACHE_DEFAULT_TIMEOUT = int(os.environ.get('CACHE_DEFAULT_TIMEOUT', 3600))  # 1 hour

# Logging Configuration 
LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
LOG_FILE = os.path.join(BASE_DIR, 'logs', 'app.log')

# Define settings for production vs development
if os.environ.get('FLASK_ENV') == 'production':
    DEBUG = False
    # Add any production-specific settings here 