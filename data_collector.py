"""
Main data collection script for the Stock Analysis & Prediction Platform.
This script fetches stock data, analyzes it, and saves the results to the database.
"""
import os
import logging
import time
from datetime import datetime
import argparse
import pandas as pd
from apscheduler.schedulers.background import BackgroundScheduler

from data.stock_fetcher import get_sp500_tickers, get_trending_tickers, fetch_batch_tickers
from analysis.technical_analysis import analyze_stock
from data.db_utils import (
    save_stock_info, save_historical_prices, save_earnings_data,
    save_support_resistance, save_trend_score, get_stock_count
)
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

def process_ticker_data(ticker_data):
    """
    Process data for a single ticker and save to database
    
    Args:
        ticker_data (dict): Dictionary with ticker data
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        ticker = ticker_data['info']['ticker']
        logger.info(f"Processing data for {ticker}")
        
        # Save basic stock info
        stock_id = save_stock_info(ticker_data['info'])
        
        if not stock_id:
            logger.error(f"Failed to save stock info for {ticker}")
            return False
        
        # Save historical prices
        if ticker_data['historical_data'] is not None:
            save_historical_prices(stock_id, ticker_data['historical_data'])
        
        # Save earnings data
        if ticker_data['earnings_data'] is not None:
            save_earnings_data(stock_id, ticker_data['earnings_data'])
        
        # Perform technical analysis
        analysis_results = analyze_stock(
            ticker, 
            ticker_data['historical_data'], 
            ticker_data['earnings_data']
        )
        
        if analysis_results:
            # Save support/resistance levels
            if analysis_results['support_resistance']:
                save_support_resistance(stock_id, analysis_results['support_resistance'])
            
            # Save trend scores
            if analysis_results['trend_scores']:
                save_trend_score(stock_id, analysis_results['trend_scores'])
        
        logger.info(f"Successfully processed data for {ticker}")
        return True
    except Exception as e:
        logger.error(f"Error processing data for {ticker}: {e}")
        return False

def collect_data(use_trending=True, limit=None):
    """
    Main function to collect and process stock data
    
    Args:
        use_trending (bool): Whether to use trending stocks or S&P 500
        limit (int): Maximum number of stocks to process
        
    Returns:
        int: Number of successfully processed stocks
    """
    try:
        start_time = time.time()
        
        # Get list of tickers
        if use_trending:
            tickers = get_trending_tickers(limit=limit or config.STOCK_COUNT)
            logger.info(f"Using {len(tickers)} trending tickers")
        else:
            tickers = get_sp500_tickers()
            logger.info(f"Using {len(tickers)} S&P 500 tickers")
        
        if limit and len(tickers) > limit:
            tickers = tickers[:limit]
            
        # Fetch data for tickers (in batches)
        batch_size = 10  # Process 10 tickers at a time
        successful_count = 0
        
        for i in range(0, len(tickers), batch_size):
            batch_tickers = tickers[i:i+batch_size]
            logger.info(f"Processing batch {i//batch_size + 1}/{(len(tickers) + batch_size - 1)//batch_size}")
            
            batch_results = fetch_batch_tickers(batch_tickers, max_workers=5)
            
            for ticker, data in batch_results.items():
                if data and process_ticker_data(data):
                    successful_count += 1
            
            logger.info(f"Processed {successful_count}/{len(tickers)} tickers so far")
        
        end_time = time.time()
        logger.info(f"Data collection completed in {end_time - start_time:.2f} seconds")
        logger.info(f"Successfully processed {successful_count}/{len(tickers)} tickers")
        
        return successful_count
    except Exception as e:
        logger.error(f"Error in data collection: {e}")
        return 0

def scheduled_collection():
    """Run scheduled data collection"""
    logger.info("Starting scheduled data collection")
    
    # Check if it's market hours (if configured)
    if config.MARKET_HOURS_ONLY:
        now = datetime.now()
        # Check if it's a weekday and between 9:30 AM and 4:00 PM ET
        if now.weekday() >= 5 or now.hour < 9 or (now.hour == 9 and now.minute < 30) or now.hour >= 16:
            logger.info("Outside market hours, skipping scheduled collection")
            return
    
    # Check current database size
    current_count = get_stock_count()
    
    # If we have enough stocks, just use trending
    if current_count >= config.STOCK_COUNT:
        logger.info(f"Database already has {current_count} stocks, collecting trending only")
        collect_data(use_trending=True, limit=50)  # Update top 50 trending
    else:
        # Otherwise, collect both S&P 500 and trending
        logger.info(f"Database has {current_count} stocks, collecting S&P 500 and trending")
        collect_data(use_trending=False)  # Get S&P 500
        collect_data(use_trending=True, limit=100)  # Get additional trending

def start_scheduler():
    """Start the background scheduler for periodic data collection"""
    scheduler = BackgroundScheduler()
    
    # Schedule data collection to run every day
    scheduler.add_job(
        scheduled_collection, 
        'interval', 
        hours=config.UPDATE_INTERVAL_HOURS,
        id='data_collection',
        replace_existing=True
    )
    
    scheduler.start()
    logger.info(f"Scheduler started, will run every {config.UPDATE_INTERVAL_HOURS} hours")

if __name__ == "__main__":
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Stock Analysis Data Collector")
    parser.add_argument("--trending", action="store_true", help="Use trending stocks instead of S&P 500")
    parser.add_argument("--limit", type=int, help="Limit the number of stocks to process")
    parser.add_argument("--scheduler", action="store_true", help="Start the background scheduler")
    args = parser.parse_args()
    
    # Ensure the logs directory exists
    os.makedirs(os.path.dirname(config.LOG_FILE), exist_ok=True)
    
    if args.scheduler:
        # Start the scheduler
        start_scheduler()
        
        # Run an initial collection
        logger.info("Running initial data collection")
        scheduled_collection()
        
        # Keep the script running
        try:
            while True:
                time.sleep(60)
        except (KeyboardInterrupt, SystemExit):
            logger.info("Scheduler stopped")
    else:
        # Run a single collection
        collect_data(use_trending=args.trending, limit=args.limit) 