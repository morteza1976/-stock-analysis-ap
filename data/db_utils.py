"""
Database utility functions for saving and retrieving stock data
"""
import logging
import pandas as pd
from sqlalchemy import create_engine, select, func, desc
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from datetime import datetime

from models import (
    Stock, HistoricalPrice, Earnings, SupportResistance, TrendScore, 
    WatchList, WatchListItem
)
import config

logger = logging.getLogger(__name__)

def get_engine():
    """
    Create and return a SQLAlchemy engine
    
    Returns:
        sqlalchemy.engine.Engine: Database engine
    """
    return create_engine(config.SQLALCHEMY_DATABASE_URI)

def save_stock_info(stock_data):
    """
    Save basic stock information to the database
    
    Args:
        stock_data (dict): Dictionary with stock information
        
    Returns:
        int: ID of the saved stock or None if failed
    """
    engine = get_engine()
    
    try:
        with Session(engine) as session:
            # Check if stock already exists
            existing_stock = session.query(Stock).filter_by(ticker=stock_data['ticker']).first()
            
            if existing_stock:
                # Update existing stock
                for key, value in stock_data.items():
                    if hasattr(existing_stock, key) and key != 'ticker':
                        setattr(existing_stock, key, value)
                
                stock_id = existing_stock.id
            else:
                # Create new stock
                stock = Stock(
                    ticker=stock_data['ticker'],
                    company_name=stock_data['company_name'],
                    sector=stock_data.get('sector'),
                    industry=stock_data.get('industry'),
                    country=stock_data.get('country'),
                    market_cap=stock_data.get('market_cap'),
                    last_updated=datetime.utcnow()
                )
                session.add(stock)
                session.flush()  # Generate ID
                stock_id = stock.id
                
            session.commit()
            return stock_id
    except SQLAlchemyError as e:
        logger.error(f"Database error saving stock info for {stock_data['ticker']}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error saving stock info for {stock_data['ticker']}: {e}")
        return None

def save_historical_prices(stock_id, historical_df):
    """
    Save historical prices to the database
    
    Args:
        stock_id (int): ID of the stock
        historical_df (pandas.DataFrame): DataFrame with historical price data
        
    Returns:
        bool: True if successful, False otherwise
    """
    if historical_df is None or historical_df.empty:
        logger.warning(f"No historical data to save for stock ID {stock_id}")
        return False
        
    engine = get_engine()
    
    try:
        with Session(engine) as session:
            # Delete existing data for this stock to avoid duplicates
            session.query(HistoricalPrice).filter_by(stock_id=stock_id).delete()
            session.commit()
            
            # Prepare data for bulk insert
            records = []
            for _, row in historical_df.iterrows():
                record = HistoricalPrice(
                    stock_id=stock_id,
                    date=row['Date'] if 'Date' in row else row.name,
                    open=row.get('Open'),
                    high=row.get('High'),
                    low=row.get('Low'),
                    close=row.get('Close'),
                    adjusted_close=row.get('Adj Close'),
                    volume=row.get('Volume')
                )
                records.append(record)
            
            # Bulk insert
            session.bulk_save_objects(records)
            session.commit()
            
            logger.info(f"Saved {len(records)} historical prices for stock ID {stock_id}")
            return True
    except SQLAlchemyError as e:
        logger.error(f"Database error saving historical prices for stock ID {stock_id}: {e}")
        return False
    except Exception as e:
        logger.error(f"Error saving historical prices for stock ID {stock_id}: {e}")
        return False

def save_earnings_data(stock_id, earnings_df):
    """
    Save earnings data to the database
    
    Args:
        stock_id (int): ID of the stock
        earnings_df (pandas.DataFrame): DataFrame with earnings data
        
    Returns:
        bool: True if successful, False otherwise
    """
    if earnings_df is None or earnings_df.empty:
        logger.warning(f"No earnings data to save for stock ID {stock_id}")
        return False
        
    engine = get_engine()
    
    try:
        with Session(engine) as session:
            # Delete existing data for this stock to avoid duplicates
            session.query(Earnings).filter_by(stock_id=stock_id).delete()
            session.commit()
            
            # Prepare data for bulk insert
            records = []
            for _, row in earnings_df.iterrows():
                record = Earnings(
                    stock_id=stock_id,
                    announcement_date=row['announcement_date'],
                    reported_eps=row.get('EPS'),
                    estimated_eps=row.get('EPS_Estimate'),
                    surprise=row.get('Surprise'),
                    surprise_percent=row.get('Surprise(%)'),
                    price_1d_change=row.get('price_1d_change'),
                    price_5d_change=row.get('price_5d_change')
                )
                records.append(record)
            
            # Bulk insert
            session.bulk_save_objects(records)
            session.commit()
            
            logger.info(f"Saved {len(records)} earnings records for stock ID {stock_id}")
            return True
    except SQLAlchemyError as e:
        logger.error(f"Database error saving earnings data for stock ID {stock_id}: {e}")
        return False
    except Exception as e:
        logger.error(f"Error saving earnings data for stock ID {stock_id}: {e}")
        return False

def save_support_resistance(stock_id, support_resistance_data):
    """
    Save support and resistance levels to the database
    
    Args:
        stock_id (int): ID of the stock
        support_resistance_data (dict): Dictionary with support and resistance levels
        
    Returns:
        bool: True if successful, False otherwise
    """
    if support_resistance_data is None:
        logger.warning(f"No support/resistance data to save for stock ID {stock_id}")
        return False
        
    engine = get_engine()
    
    try:
        with Session(engine) as session:
            # Create new record
            record = SupportResistance(
                stock_id=stock_id,
                date=support_resistance_data.get('date', datetime.utcnow()),
                resistance_1=support_resistance_data.get('resistance_1'),
                resistance_2=support_resistance_data.get('resistance_2'),
                support_1=support_resistance_data.get('support_1'),
                support_2=support_resistance_data.get('support_2'),
                fifty_two_week_high=support_resistance_data.get('fifty_two_week_high'),
                fifty_two_week_low=support_resistance_data.get('fifty_two_week_low'),
                ma_20=support_resistance_data.get('ma_20'),
                ma_50=support_resistance_data.get('ma_50'),
                ma_200=support_resistance_data.get('ma_200')
            )
            
            session.add(record)
            session.commit()
            
            logger.info(f"Saved support/resistance data for stock ID {stock_id}")
            return True
    except SQLAlchemyError as e:
        logger.error(f"Database error saving support/resistance for stock ID {stock_id}: {e}")
        return False
    except Exception as e:
        logger.error(f"Error saving support/resistance for stock ID {stock_id}: {e}")
        return False

def save_trend_score(stock_id, trend_score_data):
    """
    Save trend scores to the database
    
    Args:
        stock_id (int): ID of the stock
        trend_score_data (dict): Dictionary with trend scores
        
    Returns:
        bool: True if successful, False otherwise
    """
    if trend_score_data is None:
        logger.warning(f"No trend score data to save for stock ID {stock_id}")
        return False
        
    engine = get_engine()
    
    try:
        with Session(engine) as session:
            # Create new record
            record = TrendScore(
                stock_id=stock_id,
                date=trend_score_data.get('date', datetime.utcnow()),
                price_trend_score=trend_score_data.get('price_trend_score'),
                volume_trend_score=trend_score_data.get('volume_trend_score'),
                earnings_trend_score=trend_score_data.get('earnings_trend_score'),
                combined_score=trend_score_data.get('combined_score')
            )
            
            session.add(record)
            session.commit()
            
            logger.info(f"Saved trend score data for stock ID {stock_id}")
            return True
    except SQLAlchemyError as e:
        logger.error(f"Database error saving trend score for stock ID {stock_id}: {e}")
        return False
    except Exception as e:
        logger.error(f"Error saving trend score for stock ID {stock_id}: {e}")
        return False

def get_stock_by_ticker(ticker):
    """
    Get stock by ticker symbol
    
    Args:
        ticker (str): Stock ticker symbol
        
    Returns:
        Stock: Stock object or None if not found
    """
    engine = get_engine()
    
    try:
        with Session(engine) as session:
            return session.query(Stock).filter_by(ticker=ticker).first()
    except SQLAlchemyError as e:
        logger.error(f"Database error retrieving stock for ticker {ticker}: {e}")
        return None

def get_historical_prices(stock_id, limit=None):
    """
    Get historical prices for a stock
    
    Args:
        stock_id (int): ID of the stock
        limit (int): Maximum number of records to return
        
    Returns:
        list: List of HistoricalPrice objects
    """
    engine = get_engine()
    
    try:
        with Session(engine) as session:
            query = session.query(HistoricalPrice).filter_by(stock_id=stock_id).order_by(HistoricalPrice.date.desc())
            
            if limit:
                query = query.limit(limit)
                
            return query.all()
    except SQLAlchemyError as e:
        logger.error(f"Database error retrieving historical prices for stock ID {stock_id}: {e}")
        return []

def get_latest_trend_scores(limit=20):
    """
    Get latest trend scores for all stocks
    
    Args:
        limit (int): Maximum number of records to return
        
    Returns:
        list: List of (Stock, TrendScore) tuples
    """
    engine = get_engine()
    
    try:
        with Session(engine) as session:
            # Subquery to get the latest trend score date for each stock
            latest_dates = session.query(
                TrendScore.stock_id,
                func.max(TrendScore.date).label('max_date')
            ).group_by(TrendScore.stock_id).subquery()
            
            # Join with the subquery to get the latest trend score for each stock
            query = session.query(Stock, TrendScore).join(
                TrendScore,
                Stock.id == TrendScore.stock_id
            ).join(
                latest_dates,
                (TrendScore.stock_id == latest_dates.c.stock_id) & 
                (TrendScore.date == latest_dates.c.max_date)
            ).filter(
                Stock.is_active == True
            ).order_by(
                TrendScore.combined_score.desc()
            )
            
            if limit:
                query = query.limit(limit)
                
            return query.all()
    except SQLAlchemyError as e:
        logger.error(f"Database error retrieving latest trend scores: {e}")
        return []

def get_stock_count():
    """
    Get the total number of stocks in the database
    
    Returns:
        int: Number of stocks
    """
    engine = get_engine()
    
    try:
        with Session(engine) as session:
            return session.query(Stock).filter_by(is_active=True).count()
    except SQLAlchemyError as e:
        logger.error(f"Database error retrieving stock count: {e}")
        return 0

if __name__ == "__main__":
    # Configure logging for standalone execution
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # This module is meant to be imported, this block is for testing purposes only
    logger.info("Database utility module - Run this as a module import, not as a script.") 