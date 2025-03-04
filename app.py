"""
Main Flask application for the Stock Analysis & Prediction Platform.
"""
import os
import logging
from flask import Flask, render_template, jsonify, request, redirect, url_for
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

from models import Base, Stock, HistoricalPrice, Earnings, SupportResistance, TrendScore
from data.db_utils import get_latest_trend_scores, get_stock_by_ticker, get_historical_prices
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

# Create and configure the app
app = Flask(__name__)
app.config.from_object(config)

# Setup the database
engine = create_engine(config.SQLALCHEMY_DATABASE_URI)
db_session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))

# Register teardown function
@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()

# Routes
@app.route('/')
def index():
    """Home page"""
    return render_template('index.html')

@app.route('/trending')
def trending():
    """Trending stocks page"""
    # Get top trending stocks
    trending_stocks = get_latest_trend_scores(limit=20)
    return render_template('trending.html', trending_stocks=trending_stocks)

@app.route('/stocks')
def stocks():
    """List all stocks"""
    # Get all stocks
    all_stocks = db_session.query(Stock).filter_by(is_active=True).order_by(Stock.ticker).all()
    return render_template('stocks.html', stocks=all_stocks)

@app.route('/stocks/<ticker>')
def stock_detail(ticker):
    """Stock detail page"""
    # Get stock
    stock = get_stock_by_ticker(ticker)
    
    if not stock:
        return render_template('error.html', message=f"Stock '{ticker}' not found"), 404
    
    # Get related data
    historical_prices = get_historical_prices(stock.id, limit=100)
    
    # Get support/resistance
    support_resistance = db_session.query(SupportResistance).filter_by(stock_id=stock.id).order_by(SupportResistance.date.desc()).first()
    
    # Get trend scores
    trend_score = db_session.query(TrendScore).filter_by(stock_id=stock.id).order_by(TrendScore.date.desc()).first()
    
    # Get earnings data
    earnings = db_session.query(Earnings).filter_by(stock_id=stock.id).order_by(Earnings.announcement_date.desc()).all()
    
    return render_template(
        'stock_detail.html', 
        stock=stock, 
        historical_prices=historical_prices,
        support_resistance=support_resistance,
        trend_score=trend_score,
        earnings=earnings
    )

@app.route('/api/stocks')
def api_stocks():
    """API endpoint for stocks"""
    stocks = db_session.query(Stock).filter_by(is_active=True).order_by(Stock.ticker).all()
    return jsonify({
        'count': len(stocks),
        'stocks': [{'ticker': s.ticker, 'name': s.company_name} for s in stocks]
    })

@app.route('/api/stocks/<ticker>')
def api_stock_detail(ticker):
    """API endpoint for stock details"""
    stock = get_stock_by_ticker(ticker)
    
    if not stock:
        return jsonify({'error': f"Stock '{ticker}' not found"}), 404
    
    # Get related data
    historical_prices = get_historical_prices(stock.id, limit=100)
    
    # Get support/resistance
    support_resistance = db_session.query(SupportResistance).filter_by(stock_id=stock.id).order_by(SupportResistance.date.desc()).first()
    
    # Get trend scores
    trend_score = db_session.query(TrendScore).filter_by(stock_id=stock.id).order_by(TrendScore.date.desc()).first()
    
    # Get earnings data
    earnings = db_session.query(Earnings).filter_by(stock_id=stock.id).order_by(Earnings.announcement_date.desc()).all()
    
    # Build response
    response = {
        'stock': {
            'ticker': stock.ticker,
            'name': stock.company_name,
            'sector': stock.sector,
            'industry': stock.industry,
            'market_cap': stock.market_cap
        },
        'historical_prices': [
            {
                'date': hp.date.isoformat(),
                'open': hp.open,
                'high': hp.high,
                'low': hp.low,
                'close': hp.close,
                'volume': hp.volume
            } for hp in historical_prices
        ],
        'support_resistance': None,
        'trend_score': None,
        'earnings': [
            {
                'date': e.announcement_date.isoformat(),
                'reported_eps': e.reported_eps,
                'estimated_eps': e.estimated_eps,
                'surprise': e.surprise,
                'surprise_percent': e.surprise_percent,
                'price_1d_change': e.price_1d_change,
                'price_5d_change': e.price_5d_change
            } for e in earnings
        ]
    }
    
    if support_resistance:
        response['support_resistance'] = {
            'date': support_resistance.date.isoformat(),
            'resistance_1': support_resistance.resistance_1,
            'resistance_2': support_resistance.resistance_2,
            'support_1': support_resistance.support_1,
            'support_2': support_resistance.support_2,
            'fifty_two_week_high': support_resistance.fifty_two_week_high,
            'fifty_two_week_low': support_resistance.fifty_two_week_low,
            'ma_20': support_resistance.ma_20,
            'ma_50': support_resistance.ma_50,
            'ma_200': support_resistance.ma_200
        }
    
    if trend_score:
        response['trend_score'] = {
            'date': trend_score.date.isoformat(),
            'price_trend_score': trend_score.price_trend_score,
            'volume_trend_score': trend_score.volume_trend_score,
            'earnings_trend_score': trend_score.earnings_trend_score,
            'combined_score': trend_score.combined_score
        }
    
    return jsonify(response)

@app.route('/api/trending')
def api_trending():
    """API endpoint for trending stocks"""
    limit = request.args.get('limit', 20, type=int)
    trending_stocks = get_latest_trend_scores(limit=limit)
    
    return jsonify({
        'count': len(trending_stocks),
        'stocks': [
            {
                'ticker': stock.ticker,
                'name': stock.company_name,
                'sector': stock.sector,
                'combined_score': trend_score.combined_score,
                'price_trend_score': trend_score.price_trend_score,
                'volume_trend_score': trend_score.volume_trend_score,
                'earnings_trend_score': trend_score.earnings_trend_score
            } for stock, trend_score in trending_stocks
        ]
    })

@app.errorhandler(404)
def page_not_found(e):
    """404 error handler"""
    return render_template('error.html', message="Page not found"), 404

@app.errorhandler(500)
def server_error(e):
    """500 error handler"""
    logger.error(f"Server error: {e}")
    return render_template('error.html', message="Internal server error"), 500

if __name__ == '__main__':
    # Ensure directories exist
    os.makedirs(os.path.join(config.BASE_DIR, 'logs'), exist_ok=True)
    
    # Run the app
    app.run(host='0.0.0.0', port=config.PORT, debug=config.DEBUG) 