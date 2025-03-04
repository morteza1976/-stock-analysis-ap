"""
Database models for the Stock Analysis & Prediction Platform
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean, Text, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class Stock(Base):
    """Stock model representing basic information about a stock."""
    __tablename__ = 'stocks'

    id = Column(Integer, primary_key=True)
    ticker = Column(String(10), nullable=False, unique=True, index=True)
    company_name = Column(String(255), nullable=False)
    sector = Column(String(100))
    industry = Column(String(100))
    country = Column(String(50))
    market_cap = Column(Float)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    # Relationships
    historical_prices = relationship("HistoricalPrice", back_populates="stock", cascade="all, delete-orphan")
    earnings = relationship("Earnings", back_populates="stock", cascade="all, delete-orphan")
    support_resistance = relationship("SupportResistance", back_populates="stock", cascade="all, delete-orphan")
    trend_scores = relationship("TrendScore", back_populates="stock", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Stock(ticker='{self.ticker}', company_name='{self.company_name}')>"


class HistoricalPrice(Base):
    """Historical price data for stocks."""
    __tablename__ = 'historical_prices'

    id = Column(Integer, primary_key=True)
    stock_id = Column(Integer, ForeignKey('stocks.id'), nullable=False)
    date = Column(DateTime, nullable=False)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    adjusted_close = Column(Float)
    volume = Column(Integer)
    
    # Relationships
    stock = relationship("Stock", back_populates="historical_prices")

    # Indexes for faster querying
    __table_args__ = (
        Index('idx_historical_stock_date', 'stock_id', 'date'),
    )

    def __repr__(self):
        return f"<HistoricalPrice(ticker='{self.stock.ticker}', date='{self.date}', close='{self.close}')>"


class Earnings(Base):
    """Earnings reports for stocks."""
    __tablename__ = 'earnings'

    id = Column(Integer, primary_key=True)
    stock_id = Column(Integer, ForeignKey('stocks.id'), nullable=False)
    announcement_date = Column(DateTime, nullable=False)
    period_ending = Column(DateTime)
    reported_eps = Column(Float)
    estimated_eps = Column(Float)
    surprise = Column(Float)  # Difference between reported and estimated
    surprise_percent = Column(Float)
    
    # Price changes after earnings
    price_1d_change = Column(Float)  # 1-day price change after earnings
    price_5d_change = Column(Float)  # 5-day price change after earnings
    
    # Relationships
    stock = relationship("Stock", back_populates="earnings")

    # Indexes
    __table_args__ = (
        Index('idx_earnings_stock_date', 'stock_id', 'announcement_date'),
    )

    def __repr__(self):
        return f"<Earnings(ticker='{self.stock.ticker}', date='{self.announcement_date}', eps='{self.reported_eps}')>"


class SupportResistance(Base):
    """Support and resistance levels for stocks."""
    __tablename__ = 'support_resistance'

    id = Column(Integer, primary_key=True)
    stock_id = Column(Integer, ForeignKey('stocks.id'), nullable=False)
    date = Column(DateTime, nullable=False)  # Date these levels were calculated
    
    # Key price levels
    resistance_1 = Column(Float)
    resistance_2 = Column(Float)
    support_1 = Column(Float)
    support_2 = Column(Float)
    fifty_two_week_high = Column(Float)
    fifty_two_week_low = Column(Float)
    
    # Moving averages
    ma_20 = Column(Float)  # 20-day moving average
    ma_50 = Column(Float)  # 50-day moving average
    ma_200 = Column(Float)  # 200-day moving average
    
    # Relationships
    stock = relationship("Stock", back_populates="support_resistance")

    def __repr__(self):
        return f"<SupportResistance(ticker='{self.stock.ticker}', date='{self.date}')>"


class TrendScore(Base):
    """Trend scores for ranking stocks."""
    __tablename__ = 'trend_scores'

    id = Column(Integer, primary_key=True)
    stock_id = Column(Integer, ForeignKey('stocks.id'), nullable=False)
    date = Column(DateTime, nullable=False)
    
    # Trend indicators
    price_trend_score = Column(Float)  # Score based on price momentum
    volume_trend_score = Column(Float)  # Score based on volume changes
    earnings_trend_score = Column(Float)  # Score based on earnings surprises
    combined_score = Column(Float)  # Overall trend score
    
    # Relationships
    stock = relationship("Stock", back_populates="trend_scores")

    # Indexes
    __table_args__ = (
        Index('idx_trend_stock_date', 'stock_id', 'date'),
    )

    def __repr__(self):
        return f"<TrendScore(ticker='{self.stock.ticker}', date='{self.date}', score='{self.combined_score}')>"


class WatchList(Base):
    """User watchlist for tracking specific stocks."""
    __tablename__ = 'watchlists'

    id = Column(Integer, primary_key=True)
    user_id = Column(String(50), nullable=False)  # Could be enhanced with a proper User model
    name = Column(String(100), nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<WatchList(name='{self.name}', user='{self.user_id}')>"


class WatchListItem(Base):
    """Individual stocks in a watchlist."""
    __tablename__ = 'watchlist_items'

    id = Column(Integer, primary_key=True)
    watchlist_id = Column(Integer, ForeignKey('watchlists.id'), nullable=False)
    stock_id = Column(Integer, ForeignKey('stocks.id'), nullable=False)
    added_at = Column(DateTime, default=datetime.utcnow)
    notes = Column(Text)

    # Indexes
    __table_args__ = (
        Index('idx_watchlist_stock', 'watchlist_id', 'stock_id', unique=True),
    )

    def __repr__(self):
        return f"<WatchListItem(watchlist_id='{self.watchlist_id}', stock_id='{self.stock_id}')>" 