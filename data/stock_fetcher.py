"""
Stock data fetcher module for retrieving financial data from various sources
"""
import logging
import pandas as pd
import yfinance as yf
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm
import time

logger = logging.getLogger(__name__)

def get_sp500_tickers():
    """
    Fetch S&P 500 tickers from Wikipedia
    
    Returns:
        list: List of ticker symbols
    """
    try:
        url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
        tables = pd.read_html(url)
        sp500_table = tables[0]
        tickers = sp500_table['Symbol'].tolist()
        
        # Clean up tickers (replace dots with hyphens as per Yahoo Finance format)
        tickers = [ticker.replace('.', '-') for ticker in tickers]
        
        logger.info(f"Retrieved {len(tickers)} S&P 500 tickers")
        return tickers
    except Exception as e:
        logger.error(f"Error fetching S&P 500 tickers: {e}")
        return []

def get_trending_tickers(limit=100):
    """
    Fetch most active/trending tickers from Yahoo Finance
    
    Args:
        limit (int): Maximum number of tickers to return
        
    Returns:
        list: List of ticker symbols
    """
    try:
        urls = [
            "https://finance.yahoo.com/most-active",
            "https://finance.yahoo.com/trending-tickers"
        ]
        
        all_tickers = []
        
        for url in urls:
            tables = pd.read_html(url)
            tickers = tables[0]['Symbol'].tolist()
            all_tickers.extend(tickers)
        
        # Remove duplicates
        unique_tickers = list(dict.fromkeys(all_tickers))
        
        # Limit the number of tickers
        trending_tickers = unique_tickers[:limit]
        
        logger.info(f"Retrieved {len(trending_tickers)} trending tickers")
        return trending_tickers
    except Exception as e:
        logger.error(f"Error fetching trending tickers: {e}")
        return []

def get_stock_info(ticker):
    """
    Get basic information about a stock
    
    Args:
        ticker (str): Stock ticker symbol
        
    Returns:
        dict: Stock information or None if error
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        # Extract relevant information
        stock_info = {
            'ticker': ticker,
            'company_name': info.get('shortName', info.get('longName', '')),
            'sector': info.get('sector', ''),
            'industry': info.get('industry', ''),
            'country': info.get('country', ''),
            'market_cap': info.get('marketCap', 0),
            'last_updated': datetime.utcnow()
        }
        
        return stock_info
    except Exception as e:
        logger.error(f"Error fetching info for {ticker}: {e}")
        return None

def get_historical_data(ticker, period="2y"):
    """
    Get historical price data for a stock
    
    Args:
        ticker (str): Stock ticker symbol
        period (str): Time period (e.g., "2y" for 2 years)
        
    Returns:
        pandas.DataFrame: Historical price data or None if error
    """
    try:
        stock = yf.Ticker(ticker)
        hist_data = stock.history(period=period)
        
        # Reset index to make date a column
        hist_data = hist_data.reset_index()
        
        # Add ticker column
        hist_data['ticker'] = ticker
        
        return hist_data
    except Exception as e:
        logger.error(f"Error fetching historical data for {ticker}: {e}")
        return None

def get_earnings_data(ticker):
    """
    Get earnings data for a stock
    
    Args:
        ticker (str): Stock ticker symbol
        
    Returns:
        pandas.DataFrame: Earnings data or None if error
    """
    try:
        stock = yf.Ticker(ticker)
        
        # Get earnings dates
        earnings_dates = stock.earnings_dates
        
        if earnings_dates is None or earnings_dates.empty:
            logger.warning(f"No earnings data available for {ticker}")
            return None
        
        # Reset index to make date a column
        earnings_df = earnings_dates.reset_index()
        earnings_df = earnings_df.rename(columns={'index': 'announcement_date'})
        
        # Add ticker column
        earnings_df['ticker'] = ticker
        
        # Fetch price changes after earnings
        price_changes = calculate_post_earnings_movement(ticker, earnings_df['announcement_date'].tolist())
        
        if price_changes:
            earnings_df = pd.merge(
                earnings_df, 
                price_changes, 
                on='announcement_date', 
                how='left'
            )
        
        return earnings_df
    except Exception as e:
        logger.error(f"Error fetching earnings data for {ticker}: {e}")
        return None

def calculate_post_earnings_movement(ticker, announcement_dates, days=(1, 5)):
    """
    Calculate price movement after earnings announcements
    
    Args:
        ticker (str): Stock ticker symbol
        announcement_dates (list): List of earnings announcement dates
        days (tuple): Days to calculate price change (e.g., (1, 5) for 1 and 5 days)
        
    Returns:
        pandas.DataFrame: DataFrame with price changes or None if error
    """
    try:
        # Get historical data
        stock = yf.Ticker(ticker)
        
        # Calculate maximum date range needed
        max_days = max(days)
        start_date = min(announcement_dates) - timedelta(days=1)
        end_date = max(announcement_dates) + timedelta(days=max_days + 1)
        
        # Get daily price data
        hist_data = stock.history(start=start_date, end=end_date)
        
        if hist_data.empty:
            logger.warning(f"No historical data available for {ticker} after earnings")
            return None
        
        results = []
        
        for announcement_date in announcement_dates:
            try:
                # Find the exact date or the next trading day
                closest_date = announcement_date
                while closest_date not in hist_data.index and closest_date <= announcement_date + timedelta(days=3):
                    closest_date += timedelta(days=1)
                
                if closest_date not in hist_data.index:
                    continue
                
                # Calculate price changes
                price_changes = {'announcement_date': announcement_date}
                
                for day in days:
                    future_date = closest_date
                    days_added = 0
                    
                    # Find the date day trading days in the future
                    while days_added < day and future_date < announcement_date + timedelta(days=day + 5):
                        future_date += timedelta(days=1)
                        if future_date in hist_data.index:
                            days_added += 1
                    
                    if future_date in hist_data.index:
                        price_change = (hist_data.loc[future_date, 'Close'] - hist_data.loc[closest_date, 'Close']) / hist_data.loc[closest_date, 'Close']
                        price_changes[f'price_{day}d_change'] = price_change * 100  # as percentage
                    
                results.append(price_changes)
            except Exception as e:
                logger.warning(f"Error calculating price change for {ticker} on {announcement_date}: {e}")
                continue
        
        if results:
            return pd.DataFrame(results)
        return None
    except Exception as e:
        logger.error(f"Error calculating post-earnings movement for {ticker}: {e}")
        return None

def fetch_data_for_ticker(ticker):
    """
    Fetch all relevant data for a single ticker
    
    Args:
        ticker (str): Stock ticker symbol
        
    Returns:
        dict: Dictionary containing all stock data or None if error
    """
    try:
        logger.info(f"Fetching data for {ticker}")
        
        # Add delay to avoid rate limiting
        time.sleep(0.5)
        
        # Get basic stock information
        stock_info = get_stock_info(ticker)
        
        if not stock_info:
            logger.warning(f"Could not fetch basic info for {ticker}, skipping")
            return None
        
        # Get historical price data
        historical_data = get_historical_data(ticker)
        
        # Get earnings data
        earnings_data = get_earnings_data(ticker)
        
        return {
            'info': stock_info,
            'historical_data': historical_data,
            'earnings_data': earnings_data
        }
    except Exception as e:
        logger.error(f"Error processing ticker {ticker}: {e}")
        return None

def fetch_batch_tickers(tickers, max_workers=5):
    """
    Fetch data for multiple tickers in parallel
    
    Args:
        tickers (list): List of ticker symbols
        max_workers (int): Maximum number of parallel workers
        
    Returns:
        dict: Dictionary mapping tickers to their data
    """
    results = {}
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Use tqdm for progress tracking
        future_to_ticker = {executor.submit(fetch_data_for_ticker, ticker): ticker for ticker in tickers}
        
        for future in tqdm(future_to_ticker, desc="Fetching stock data", unit="ticker"):
            ticker = future_to_ticker[future]
            try:
                data = future.result()
                if data:
                    results[ticker] = data
            except Exception as e:
                logger.error(f"Error fetching data for {ticker}: {e}")
    
    logger.info(f"Successfully fetched data for {len(results)}/{len(tickers)} tickers")
    return results

if __name__ == "__main__":
    # Configure logging for standalone execution
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Example usage
    sp500_tickers = get_sp500_tickers()
    trending_tickers = get_trending_tickers(limit=10)
    
    print(f"S&P 500 Tickers (first 5): {sp500_tickers[:5]}")
    print(f"Trending Tickers (first 5): {trending_tickers[:5]}")
    
    # Fetch data for a few tickers as a test
    test_tickers = trending_tickers[:3]
    results = fetch_batch_tickers(test_tickers, max_workers=3)
    
    for ticker, data in results.items():
        if data and data['historical_data'] is not None:
            print(f"{ticker} - Last close: ${data['historical_data']['Close'].iloc[-1]:.2f}")
            
        if data and data['earnings_data'] is not None:
            print(f"{ticker} - Last earnings date: {data['earnings_data']['announcement_date'].iloc[0]}") 