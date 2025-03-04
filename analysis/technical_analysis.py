"""
Technical analysis module for calculating indicators, support/resistance levels, and trend scores.
"""
import logging
import pandas as pd
import numpy as np
from datetime import datetime

logger = logging.getLogger(__name__)

def calculate_moving_averages(df, windows=[20, 50, 200]):
    """
    Calculate moving averages for the given DataFrame
    
    Args:
        df (pandas.DataFrame): DataFrame with price data
        windows (list): List of periods for moving averages
        
    Returns:
        pandas.DataFrame: DataFrame with moving averages added
    """
    try:
        result_df = df.copy()
        
        for window in windows:
            result_df[f'ma_{window}'] = result_df['Close'].rolling(window=window).mean()
            
        return result_df
    except Exception as e:
        logger.error(f"Error calculating moving averages: {e}")
        return df

def calculate_support_resistance(df, ticker, window=252, num_levels=2):
    """
    Calculate support and resistance levels
    
    Args:
        df (pandas.DataFrame): DataFrame with price data
        ticker (str): Stock ticker symbol
        window (int): Window size for calculation (default: 252 trading days ~ 1 year)
        num_levels (int): Number of support/resistance levels to identify
        
    Returns:
        dict: Dictionary with support and resistance levels
    """
    try:
        # Calculate 52-week high and low
        high_52w = df['High'].rolling(window=window).max().iloc[-1]
        low_52w = df['Low'].rolling(window=window).min().iloc[-1]
        
        # Calculate moving averages
        ma_df = calculate_moving_averages(df)
        
        # Get the most recent values
        latest = ma_df.iloc[-1]
        
        # Calculate additional support/resistance levels
        price_range = high_52w - low_52w
        
        # Naively calculate resistance levels above current price
        current_price = latest['Close']
        
        resistances = []
        supports = []
        
        # Find local maxima for resistance and minima for support
        for i in range(num_levels):
            # Simple method: divide the range into segments
            resistance_level = current_price + ((i + 1) / (num_levels + 1)) * (high_52w - current_price)
            support_level = current_price - ((i + 1) / (num_levels + 1)) * (current_price - low_52w)
            
            resistances.append(resistance_level)
            supports.append(support_level)
        
        # Sort levels
        resistances.sort()
        supports.sort(reverse=True)
        
        # Create result dictionary
        result = {
            'ticker': ticker,
            'date': datetime.now(),
            'fifty_two_week_high': high_52w,
            'fifty_two_week_low': low_52w,
            'ma_20': latest.get('ma_20'),
            'ma_50': latest.get('ma_50'),
            'ma_200': latest.get('ma_200')
        }
        
        # Add resistance levels
        for i, level in enumerate(resistances):
            result[f'resistance_{i+1}'] = level
            
        # Add support levels
        for i, level in enumerate(supports):
            result[f'support_{i+1}'] = level
            
        return result
    except Exception as e:
        logger.error(f"Error calculating support/resistance for {ticker}: {e}")
        return None

def calculate_trend_score(historical_df, earnings_df=None, ticker=None):
    """
    Calculate trend scores for ranking stocks
    
    Args:
        historical_df (pandas.DataFrame): DataFrame with historical price data
        earnings_df (pandas.DataFrame): DataFrame with earnings data (optional)
        ticker (str): Stock ticker symbol
        
    Returns:
        dict: Dictionary with trend scores
    """
    try:
        if historical_df is None or historical_df.empty:
            logger.warning(f"No historical data available for trend score calculation for {ticker}")
            return None
            
        # Latest price data
        latest_price = historical_df.iloc[-1]['Close']
        
        # Price trend score (based on recent performance)
        # 1. Calculate returns for different periods
        returns = {}
        
        for period, days in [('1d', 1), ('1w', 5), ('1m', 20), ('3m', 60)]:
            if len(historical_df) > days:
                past_price = historical_df.iloc[-days-1]['Close'] if days < len(historical_df) else historical_df.iloc[0]['Close']
                returns[period] = (latest_price - past_price) / past_price
            else:
                returns[period] = 0
        
        # 2. Weight the returns (more weight to recent periods)
        weights = {'1d': 0.3, '1w': 0.3, '1m': 0.2, '3m': 0.2}
        price_trend_score = sum(returns[period] * weights[period] for period in weights) * 100
        
        # Volume trend score
        recent_volume = historical_df.iloc[-5:]['Volume'].mean()
        baseline_volume = historical_df.iloc[-30:-5]['Volume'].mean() if len(historical_df) > 30 else historical_df['Volume'].mean()
        
        if baseline_volume > 0:
            volume_trend_score = (recent_volume / baseline_volume - 1) * 100
        else:
            volume_trend_score = 0
        
        # Earnings trend score (if available)
        earnings_trend_score = 0
        if earnings_df is not None and not earnings_df.empty and 'surprise_percent' in earnings_df.columns:
            recent_surprises = earnings_df.head(3)  # Last 3 earnings
            if not recent_surprises.empty:
                # Average surprise percentage
                avg_surprise = recent_surprises['surprise_percent'].mean()
                earnings_trend_score = avg_surprise
        
        # Combined score (weighted average)
        combined_score = (
            0.5 * price_trend_score +
            0.3 * volume_trend_score +
            0.2 * earnings_trend_score
        )
        
        return {
            'ticker': ticker,
            'date': datetime.now(),
            'price_trend_score': price_trend_score,
            'volume_trend_score': volume_trend_score,
            'earnings_trend_score': earnings_trend_score,
            'combined_score': combined_score
        }
    except Exception as e:
        logger.error(f"Error calculating trend score for {ticker}: {e}")
        return None

def analyze_price_action_after_earnings(historical_df, earnings_df, ticker=None):
    """
    Analyze how price typically moves after earnings announcements
    
    Args:
        historical_df (pandas.DataFrame): DataFrame with historical price data
        earnings_df (pandas.DataFrame): DataFrame with earnings data
        ticker (str): Stock ticker symbol
        
    Returns:
        dict: Dictionary with earnings price action analysis
    """
    try:
        if earnings_df is None or earnings_df.empty:
            logger.warning(f"No earnings data available for {ticker}")
            return None
            
        # Calculate average price change after earnings
        if 'price_1d_change' in earnings_df.columns and 'price_5d_change' in earnings_df.columns:
            avg_1d_change = earnings_df['price_1d_change'].mean()
            avg_5d_change = earnings_df['price_5d_change'].mean()
            
            # Calculate impact of earnings surprise on price change
            if 'surprise_percent' in earnings_df.columns:
                # Group by positive vs negative surprises
                positive_surprises = earnings_df[earnings_df['surprise_percent'] > 0]
                negative_surprises = earnings_df[earnings_df['surprise_percent'] < 0]
                
                # Calculate average price changes for each group
                avg_1d_after_positive = positive_surprises['price_1d_change'].mean() if not positive_surprises.empty else None
                avg_5d_after_positive = positive_surprises['price_5d_change'].mean() if not positive_surprises.empty else None
                
                avg_1d_after_negative = negative_surprises['price_1d_change'].mean() if not negative_surprises.empty else None
                avg_5d_after_negative = negative_surprises['price_5d_change'].mean() if not negative_surprises.empty else None
                
                # Correlation between surprise percent and price changes
                surprise_1d_corr = earnings_df[['surprise_percent', 'price_1d_change']].corr().iloc[0, 1] if len(earnings_df) > 1 else None
                surprise_5d_corr = earnings_df[['surprise_percent', 'price_5d_change']].corr().iloc[0, 1] if len(earnings_df) > 1 else None
                
                return {
                    'ticker': ticker,
                    'avg_1d_change': avg_1d_change,
                    'avg_5d_change': avg_5d_change,
                    'avg_1d_after_positive_surprise': avg_1d_after_positive,
                    'avg_5d_after_positive_surprise': avg_5d_after_positive,
                    'avg_1d_after_negative_surprise': avg_1d_after_negative,
                    'avg_5d_after_negative_surprise': avg_5d_after_negative,
                    'surprise_1d_correlation': surprise_1d_corr,
                    'surprise_5d_correlation': surprise_5d_corr,
                    'earnings_count': len(earnings_df)
                }
            else:
                return {
                    'ticker': ticker,
                    'avg_1d_change': avg_1d_change,
                    'avg_5d_change': avg_5d_change,
                    'earnings_count': len(earnings_df)
                }
        else:
            logger.warning(f"Price change data not available in earnings DataFrame for {ticker}")
            return None
    except Exception as e:
        logger.error(f"Error analyzing price action after earnings for {ticker}: {e}")
        return None

def analyze_stock(ticker, historical_df, earnings_df=None):
    """
    Perform complete technical analysis for a stock
    
    Args:
        ticker (str): Stock ticker symbol
        historical_df (pandas.DataFrame): DataFrame with historical price data
        earnings_df (pandas.DataFrame): DataFrame with earnings data (optional)
        
    Returns:
        dict: Dictionary with all analysis results
    """
    try:
        if historical_df is None or historical_df.empty:
            logger.warning(f"No historical data available for analysis for {ticker}")
            return None
            
        # Calculate support/resistance levels
        support_resistance = calculate_support_resistance(historical_df, ticker)
        
        # Calculate trend scores
        trend_scores = calculate_trend_score(historical_df, earnings_df, ticker)
        
        # Analyze price action after earnings
        earnings_analysis = None
        if earnings_df is not None and not earnings_df.empty:
            earnings_analysis = analyze_price_action_after_earnings(historical_df, earnings_df, ticker)
        
        return {
            'ticker': ticker,
            'support_resistance': support_resistance,
            'trend_scores': trend_scores,
            'earnings_analysis': earnings_analysis
        }
    except Exception as e:
        logger.error(f"Error performing technical analysis for {ticker}: {e}")
        return None

if __name__ == "__main__":
    # Configure logging for standalone execution
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # This module is meant to be imported, this block is for testing purposes only
    logger.info("Technical analysis module - Run this as a module import, not as a script.") 