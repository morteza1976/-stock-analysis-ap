# Automated Stock Analysis & Prediction Platform

A comprehensive system for analyzing 500 trending stocks, tracking earnings trends, price action, support/resistance levels, and market cap analysis.

## Project Overview

This platform gathers financial data for trending stocks, analyzes market patterns, and provides insights through a web dashboard. It collects both historical and live data to offer valuable insights into market trends and potential investment opportunities.

## Features

- **Data Collection**: Gathers historical prices, earnings data, and market information for 500 trending stocks
- **Technical Analysis**: Calculates support/resistance levels, trend scores, and price action after earnings
- **Market Insights**: Analyzes market cap and sector performance
- **Interactive Dashboard**: Web interface with customizable charts and watchlists
- **Automated Updates**: Scheduled data refreshes to maintain current information

## Project Structure

```
stock_analysis/
│
├── data/               # Raw and processed data storage
├── models/             # Database models and ML prediction models
├── analysis/           # Analysis scripts and utilities
├── web/                # Flask web application
├── static/             # CSS, JavaScript, and static assets
├── templates/          # HTML templates for web interface
├── logs/               # Application logs
│
├── config.py           # Configuration settings
├── app.py              # Main application entry point
├── db_setup.py         # Database initialization script
├── requirements.txt    # Project dependencies
└── README.md           # Project documentation
```

## Installation & Setup

1. Clone the repository:
   ```
   git clone <repository-url>
   cd stock_analysis
   ```

2. Create a virtual environment:
   ```
   python -m venv venv
   venv\Scripts\activate  # On Windows
   source venv/bin/activate  # On Unix/macOS
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Set up the database:
   ```
   python db_setup.py
   ```

5. Run the application:
   ```
   python app.py
   ```

## Usage

After starting the application, navigate to `http://localhost:5000` in your web browser to access the dashboard. From there, you can:

- Browse the list of trending stocks
- View detailed analysis for individual stocks
- Explore earnings trends and price action
- Access support and resistance levels
- Analyze market cap distribution

## Future Enhancements

- Machine learning models for price prediction
- Social media sentiment analysis
- Portfolio optimization suggestions
- Telegram bot integration for real-time alerts
- Options flow analysis

## License

[MIT License](LICENSE)

## Contact

For questions or feedback, please contact [Your Contact Information] 