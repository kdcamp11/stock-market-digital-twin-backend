# 🏦 Stock Market Digital Twin

A comprehensive, production-ready stock market analysis and trading simulation system powered by AI agents, real-time market data, and advanced technical analysis.

## 🌟 Features

### 🤖 AI-Powered Stock Agent
- Intelligent decision-making based on multiple technical indicators
- Natural language interaction for stock analysis
- Real-time market sentiment analysis
- Confidence-scored buy/sell/hold recommendations

### 📊 Advanced Technical Analysis
- **Complete Indicator Suite**: MACD, Bollinger Bands, VWAP, TTM Squeeze, Stochastic RSI, ATR, Fibonacci zones
- **Multi-Signal Analysis**: Combines multiple indicators for stronger decision confidence
- **Real-time Signal Generation**: Live buy/sell/hold signals with strength scoring
- **Historical Backtesting**: Performance analysis with trade history and metrics

### 📈 Real-Time Market Data
- **Alpaca Market Data Integration**: Live quotes, trades, and historical data
- **WebSocket Streaming**: Real-time price updates for multiple symbols
- **Dynamic Symbol Selection**: Add/remove symbols for live monitoring
- **Current 2025 Market Data**: Fresh, up-to-date pricing and analysis

### 💼 Portfolio Simulation
- **Virtual Trading**: Simulate buy/sell decisions with realistic costs
- **Performance Tracking**: Portfolio value, returns, and trade history
- **Strategy Backtesting**: Test different trading strategies historically
- **Risk Analysis**: Drawdown, Sharpe ratio, and win rate calculations

### 📋 Options Analysis
- **Options Chain Data**: Strike prices, expiration dates, bid/ask spreads
- **Greeks Calculation**: Delta, Gamma, Theta, Vega using Black-Scholes model
- **Sentiment Analysis**: Put/call ratio, max pain, implied volatility
- **Strategy Recommendations**: Bullish, bearish, and neutral options strategies

### 🎨 Modern Web Interface
- **React Frontend**: Responsive, modern UI with Material-UI components
- **Multi-Tab Interface**: Dashboard, Alerts, Strategy Testing, Agent Chat, Technical Analysis
- **Live Price Streaming**: Real-time updates with WebSocket connectivity
- **Interactive Charts**: Visual representation of indicators and signals

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- Node.js 16+
- Alpaca Markets API account (free paper trading available)

### 1. Clone the Repository
```bash
git clone <your-repo-url>
cd "Stock Market Digital Twin"
```

### 2. Set Up Environment Variables
```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your Alpaca API credentials
ALPACA_API_KEY=your_alpaca_api_key_here
ALPACA_API_SECRET=your_alpaca_api_secret_here
```

### 3. Install Python Dependencies
```bash
pip install fastapi uvicorn pandas alpaca-py pandas-ta sqlite3 asyncio
```

### 4. Install Frontend Dependencies
```bash
cd ui
npm install
cd ..
```

### 5. Ingest Fresh Market Data
```bash
# Fetch current market data from Alpaca
python3 ingest_fresh_data.py
```

### 6. Start the Backend Server
```bash
# Start the API server
python3 run_api.py
```

### 7. Start the Frontend
```bash
# In a new terminal
cd ui
npm start
```

### 8. Access the Application
- **Frontend**: http://localhost:3000
- **API Documentation**: http://localhost:8000/docs
- **WebSocket**: ws://localhost:8000/ws/realtime

## 📚 API Endpoints

### Core Endpoints
- `GET /api/twin/latest` - Latest twin states for all symbols
- `POST /api/agent` - AI agent chat and decision making
- `GET /api/symbols` - Available symbols in database
- `GET /api/realtime/{symbol}` - Real-time quote for symbol
- `POST /api/add_ticker` - Add new symbol for tracking

### Technical Analysis
- `GET /api/technical/{symbol}` - Complete technical analysis
- `GET /api/backtest/{symbol}` - Historical backtest results
- `GET /api/chart/{symbol}` - Chart data with indicators

### Options Analysis
- `GET /api/options/{symbol}` - Options chain data
- `GET /api/options/analysis/{symbol}` - Options sentiment analysis
- `GET /api/options/strategies/{symbol}` - Strategy recommendations

### Portfolio Management
- `POST /api/portfolio/create` - Create new portfolio
- `POST /api/portfolio/backtest` - Run strategy backtest

## 🏗️ Architecture

### Backend (Python/FastAPI)
- **FastAPI**: High-performance async web framework
- **Alpaca Integration**: Real-time and historical market data
- **SQLite Database**: Local storage for market data and analysis
- **Technical Indicators**: pandas-ta for comprehensive analysis
- **AI Agent**: Intelligent decision-making system

### Frontend (React)
- **React 18**: Modern component-based UI
- **Material-UI**: Professional design system
- **WebSocket Client**: Real-time data streaming
- **Axios**: HTTP client for API communication
- **Custom Hooks**: Reusable logic for live data

### Data Flow
1. **Alpaca API** → Market data ingestion → **SQLite Database**
2. **Database** → Technical analysis → **AI Agent decisions**
3. **Backend API** → Real-time updates → **React Frontend**
4. **WebSocket** → Live streaming → **Dynamic UI updates**

## 🔧 Configuration

### Environment Variables
```bash
# Required: Alpaca API credentials
ALPACA_API_KEY=your_key_here
ALPACA_API_SECRET=your_secret_here

# Optional: Environment (paper/live)
ALPACA_ENVIRONMENT=paper
```

### Frontend Configuration
```bash
# React app API URL
REACT_APP_API_URL=http://localhost:8000
```

## 📊 Current Market Data

The system includes fresh July 2025 market data with current prices:
- **AAPL**: $211.18
- **MSFT**: $510.05
- **TSLA**: $329.65
- **GOOGL**: $185.06
- **AMZN**: $226.13
- **META**: $704.28
- **NVDA**: $172.41

## 🎯 Use Cases

### For Traders
- Real-time market analysis and signals
- Portfolio simulation and backtesting
- Options strategy recommendations
- AI-powered decision support

### For Developers
- Complete financial data pipeline
- Real-time WebSocket implementation
- Advanced technical analysis algorithms
- Modern React/FastAPI architecture

### For Researchers
- Historical market data analysis
- Technical indicator effectiveness studies
- AI agent decision pattern analysis
- Options sentiment correlation research

## 🛠️ Development

### Adding New Indicators
1. Extend `TechnicalIndicators` class in `modeling/technical_indicators.py`
2. Add calculation logic and signal generation
3. Update frontend components for visualization

### Adding New Symbols
```python
# Use the data ingestion script
python3 ingest_fresh_data.py
# Or via API
POST /api/add_ticker {"symbol": "NVDA"}
```

### Customizing AI Agent
- Modify decision logic in `modeling/agent.py`
- Adjust confidence scoring and signal weights
- Add new reasoning patterns

## 🔒 Security

- ✅ API credentials stored in environment variables
- ✅ CORS properly configured for development
- ✅ Input validation on all endpoints
- ✅ Error handling prevents information leakage
- ✅ Database queries use parameterized statements

## 📈 Performance

- **Real-time Updates**: WebSocket streaming for live data
- **Efficient Database**: SQLite with indexed queries
- **Async Operations**: Non-blocking API calls
- **Caching**: Strategic caching of technical indicators
- **Optimized Frontend**: React hooks for efficient re-renders

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **Alpaca Markets** for providing excellent market data API
- **pandas-ta** for comprehensive technical analysis library
- **FastAPI** for the high-performance web framework
- **React** for the modern frontend framework

## 📞 Support

For questions, issues, or feature requests:
1. Check the API documentation at `/docs`
2. Review the code comments and docstrings
3. Open an issue on GitHub

---

**Built with ❤️ for the trading community**
