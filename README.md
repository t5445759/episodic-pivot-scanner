# Episodic Pivot Stock Scanner

A comprehensive Python framework for scanning U.S. stocks for episodic pivot patterns (gap up + high volume), with built-in backtesting, paper trading, alerts, and news catalyst analysis.

🚀 **Key Features:**
- **Real-Time Scanner** - Detects gap up stocks with unusual high relative volume
- **Historical Backtesting** - Validate strategy performance on historical data
- **Paper Trading** - Risk-free simulated trading with P&L tracking
- **Alert System** - Email, SMS, and webhook notifications
- **News Catalyst Analysis** - Sentiment analysis and news aggregation
- **Web Dashboard** - Interactive UI for monitoring and managing trades
- **CLI Tool** - Command-line interface for all operations
- **Database** - SQLite or PostgreSQL for persistent data storage
- **Docker Support** - Containerized deployment ready

---

## Installation

### Prerequisites
- Python 3.9+
- pip or conda
- Git

### Quick Start

1. **Clone the repository:**
   ```bash
   git clone https://github.com/t5445759/episodic-pivot-scanner.git
   cd episodic-pivot-scanner
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and settings
   ```

5. **Initialize database:**
   ```bash
   python -c "from src.db.session import init_db; init_db()"
   ```

---

## Usage

### Web API & Dashboard

Start the FastAPI server with interactive dashboard:

```bash
python run_api.py
```

Then visit:
- **API Docs:** http://localhost:8000/docs
- **Dashboard:** http://localhost:8000/dashboard
- **Health Check:** http://localhost:8000/health

### CLI Commands

#### Run Real-Time Scanner
```bash
python run_cli.py scan --universe sp500 --limit 50
```

#### Backtest a Strategy
```bash
python run_cli.py backtest TSLA --start-date 2023-01-01 --end-date 2024-01-01
```

#### Paper Trading
```bash
python run_cli.py paper-buy --ticker AAPL --price 150.00 --shares 10
python run_cli.py paper-sell --ticker AAPL --price 155.00 --shares 10
```

#### Get Stock News & Sentiment
```bash
python run_cli.py news --ticker NVDA --company-name "NVIDIA Corporation"
```

#### View Scan History
```bash
python run_cli.py history --days 7 --limit 50
```

#### View Configuration
```bash
python run_cli.py config-show --output config.json
```

### Continuous Scanning (Production)

Run the orchestrator in continuous mode:

```bash
python run_orchestrator.py
```

This will:
- Scan stocks at configured intervals
- Send real-time alerts via email/SMS/webhook
- Store results in database
- Run continuously during market hours

---

## Configuration

Edit `.env` file to customize:

### Scanner Settings
```env
# Price filters
MIN_PRICE=5.0
MAX_PRICE=500.0

# Market cap (in dollars)
MIN_MARKET_CAP=50000000        # $50M
MAX_MARKET_CAP=10000000000     # $10B

# Gap detection
MIN_GAP_PCT=10.0               # 10% gap

# Volume filters
MIN_RELATIVE_VOLUME=5.0        # 5x average volume
MIN_VOLUME=500000              # Minimum shares
MIN_AVG_DOLLAR_VOLUME=10000000 # $10M daily average

# Scanning
SCAN_INTERVAL_SECONDS=60
```

### Alert Settings
```env
# Email alerts
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_EMAIL=your-email@gmail.com
SMTP_PASSWORD=your-app-password
ALERT_RECIPIENTS=user@example.com,another@example.com

# SMS alerts (Twilio)
TWILIO_ACCOUNT_SID=your_sid
TWILIO_AUTH_TOKEN=your_token
TWILIO_PHONE_FROM=+1234567890
TWILIO_PHONE_TO=+0987654321
```

### Data Sources
```env
# Alpaca API (optional, for live data)
ALPACA_API_KEY=your_key
ALPACA_SECRET_KEY=your_secret
ALPACA_BASE_URL=https://paper-trading.alpaca.markets

# News API
NEWSAPI_KEY=your_key

# Database
DATABASE_URL=sqlite:///./episodic_pivot.db
```

---

## Docker Deployment

### Quick Start
```bash
# Build image
docker build -t episodic-pivot-scanner .

# Run API server
docker-compose up -d api

# View logs
docker-compose logs -f api

# Run with scanner
docker-compose --profile scanner up -d
```

### Environment Variables
Create `.env` file before running:
```bash
cp .env.example .env
# Edit with your settings
docker-compose up -d
```

---

## API Endpoints

### Scanning
- `POST /api/scan` - Run scan on specified tickers
- `GET /api/scan/results` - Get historical scan results
- `GET /api/scan/top` - Get top results by score

### Backtesting
- `POST /api/backtest` - Run backtest on a ticker
- `GET /api/backtest/results` - Get backtest history

### Paper Trading
- `POST /api/paper-trade/buy` - Execute paper buy order
- `POST /api/paper-trade/sell` - Execute paper sell order
- `GET /api/paper-trade/account` - Get account summary
- `GET /api/paper-trade/trades` - Get trade history

### News & Catalysts
- `GET /api/news/{ticker}` - Get news and sentiment

### System
- `GET /health` - Health check
- `GET /config` - View current configuration
- `GET /dashboard` - Interactive dashboard

---

## Filtering & Criteria

### Episodic Pivot Criteria
Stocks must meet ALL of the following:

1. **Price**: $5 - $500
2. **Market Cap**: $50M - $10B
3. **Gap Up**: ≥ 10%
4. **Relative Volume**: ≥ 5x average
5. **Volume**: ≥ 500k shares
6. **Daily $ Volume**: ≥ $10M

### Scoring
Results are ranked by composite score:
- **Gap %** (40%): Higher gaps score better
- **Relative Volume** (30%): Higher volume multiplier scores better
- **Price Action** (20%): Current day gains
- **Market Cap** (10%): Preference for liquid stocks

---

## Results Display

Each scan result includes:

| Field | Description |
|-------|-------------|
| Ticker | Stock symbol |
| Price | Current price |
| Gap % | Gap from previous close |
| Change % | Today's percentage change |
| Volume | Today's volume |
| Relative Volume | Volume relative to average |
| Market Cap | Market capitalization |
| Sector | Industry sector |
| 1W Performance | 5-day performance |
| 1M Performance | 20-day performance |
| SMA 10 | 10-day simple moving average |
| SMA 20 | 20-day simple moving average |
| Score | Composite score (0-1) |

---

## Backtesting

### Running a Backtest

```bash
python run_cli.py backtest TSLA --start-date 2023-01-01 --end-date 2024-01-01 --initial-capital 100000
```

### Backtest Results Include

- Initial & Final Capital
- Total Return %
- Buy & Hold Return %
- Excess Return %
- Number of Trades
- Win Rate %
- Average Win %
- Average Loss %
- Profit Factor
- Portfolio Value History

---

## Paper Trading

### Account Features
- Starting capital (default: $100k)
- Position tracking
- Unrealized P&L
- Trade history
- Performance metrics

### Commands

```bash
# Buy 100 shares of AAPL at $150
python run_cli.py paper-buy --ticker AAPL --price 150.00 --shares 100

# Sell 50 shares at $155
python run_cli.py paper-sell --ticker AAPL --price 155.00 --shares 50

# View account
python run_cli.py paper-account
```

---

## Alerts

Configurable alerts via:

1. **Email** - HTML formatted alerts with all details
2. **SMS** - Concise alerts via Twilio
3. **Webhooks** - JSON payload to Discord, Slack, etc.

### Alert Triggers
- Gap ≥ configured threshold (default: 10%)
- Relative volume ≥ configured threshold (default: 5x)

---

## News & Sentiment Analysis

Automatically analyzes:

- **Recent Articles**: Fetches from NewsAPI
- **Sentiment Score**: NLP-based sentiment analysis
- **Catalyst Detection**: Identifies potential news catalysts
- **Sentiment Categories**: Positive, Negative, Neutral

```bash
python run_cli.py news --ticker NVDA --company-name "NVIDIA Corporation"
```

---

## Database

### Tables

1. **scan_results** - Historical scan results
2. **alerts** - Sent alerts history
3. **paper_trades** - Paper trading transactions
4. **backtest_results** - Backtest run results
5. **news_articles** - Fetched news articles

### Querying

```python
from src.db.session import SessionLocal
from src.db.manager import DatabaseManager

db = SessionLocal()
db_manager = DatabaseManager(db)

# Get recent scans
results = db_manager.get_scan_results(ticker='AAPL', days=7)

# Get top scans by score
top_results = db_manager.get_top_scans_by_score(limit=20)

# Get backtest results
backtests = db_manager.get_backtest_results(ticker='TSLA')

db.close()
```

---

## Examples

See the `/examples` directory for:

1. **basic_scanning.py** - Simple scan example
2. **backtesting.py** - Backtest workflow
3. **paper_trading.py** - Paper trading example
4. **alerts_integration.py** - Setup alerts
5. **news_analysis.py** - News sentiment analysis
6. **full_workflow.py** - Complete end-to-end example

---

## Roadmap

- [x] Real-time gap scanner
- [x] Backtesting engine
- [x] Paper trading
- [x] Alert system
- [x] Web API & Dashboard
- [x] CLI tool
- [x] Database persistence
- [x] Docker support
- [ ] Live trading (with Alpaca/Robinhood)
- [ ] Advanced charting
- [ ] Machine learning models
- [ ] Performance optimization
- [ ] Multi-timeframe analysis

---

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

---

## Disclaimer

**For Research and Paper Trading Only**

This tool is designed for:
- Research and educational purposes
- Paper trading (simulated trading)
- Strategy development and backtesting

**NOT recommended for:**
- Live trading without extensive testing
- Real money without professional risk management
- Use without understanding the strategy

Always paper trade first and validate strategies thoroughly before any live trading.

---

## License

MIT License - See LICENSE file for details

---

## Support

For issues, questions, or suggestions:
- Open an issue on GitHub
- Check existing issues first
- Provide detailed information about your environment

---

## Resources

- [Episodic Pivot Trading Strategy](https://www.investopedia.com/terms/e/episodic.asp)
- [Gap Trading Analysis](https://www.investopedia.com/terms/g/gapping.asp)
- [Relative Volume](https://www.investopedia.com/terms/r/relative-volume.asp)
- [Backtrader Documentation](https://www.backtrader.com/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)

---

**Built with ❤️ for traders and developers**
