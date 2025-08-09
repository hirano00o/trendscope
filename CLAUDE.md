# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Trendscope is a stock price trend analysis web application that analyzes stock price uptrends and outputs the probability of stock price increases using multiple analysis methods.

### Architecture

- **Frontend**: Next.js with TypeScript - accepts stock symbols from users and displays analysis results
- **Backend**: Python 3.12+ - receives stock symbols, analyzes stock price growth rates, returns results to frontend
- **Core Library**: yfinance for stock data retrieval

## Current Development Status

**Backend Implementation Progress:**

### ✅ Implemented Modules
1. **FastAPI Application Foundation** - Fully implemented
   - CORS middleware, security headers, logging middleware
   - Error handling, health check endpoints

2. **API Endpoints** - Fully implemented
   - `/health` - Health check
   - `/api/v1/analysis/{symbol}` - Technical analysis
   - `/api/v1/comprehensive/{symbol}` - Comprehensive analysis
   - `/api/v1/historical/{symbol}` - Historical data retrieval

3. **Data Models** - Implemented (Test coverage: 68%)
   - Pydantic models: StockData, AnalysisResult, API schemas
   - With validation functionality

4. **Analysis Modules** - Implemented (insufficient testing)
   - Technical indicators: SMA, EMA, RSI, MACD, Bollinger Bands
   - Pattern recognition: Candlestick patterns, support/resistance lines
   - Volatility analysis: ATR, standard deviation, volatility regime detection
   - Machine learning predictions: Random Forest, SVM, ARIMA, ensemble methods
   - Integrated scoring: 6-category integrated analysis

### ⚠️ Current Issues
- **Low test coverage**: Overall 9% coverage
- **Syntax errors in test code**: Duplicate definitions in some test files
- **Insufficient business logic testing**: Main analysis modules have 0% test coverage

### ✅ Frontend Implementation Complete
1. **Next.js Project Foundation** - TypeScript, Tailwind CSS 3.x, PostCSS configuration, package.json setup with bun
2. **Design System & UI Components** - Radix UI integration, custom components (Button, Input, Card, Progress, Badge), responsive design system
3. **API Integration Foundation** - TanStack Query setup, comprehensive error handling, React hooks for API calls, type-safe API client
4. **Landing Page & Core Features** - Hero section, stock analysis form with validation, analysis results display components
5. **6-Category Analysis Results Display** - MetricCard, SignalBadge, ConfidenceProgress, comprehensive analysis dashboard layout
6. **Type Definition System** - Complete TypeScript interfaces for all API responses, analysis data structures, component props
7. **Japanese Stock Support** - Japanese stock symbol validation, popular Japanese stocks integration, bilingual UI support (7203.T format)
8. **🆕 Chart Features** - Recharts-based price charts, volume bars, moving averages, Bollinger Bands display
9. **Historical Data Retrieval** - useHistoricalData hook, multiple period data retrieval, prefetch functionality

**Frontend Architecture Completed:**
- ✅ Next.js 14 + TypeScript with strict mode
- ✅ Tailwind CSS 3.x design system with custom color palette
- ✅ TanStack Query for API state management with caching and retry logic
- ✅ Comprehensive error handling with user-friendly messages
- ✅ Component library with consistent styling (Button, Input, Card, Badge, Progress)
- ✅ Responsive design optimized for financial dashboard layout
- ✅ Type-safe API integration with complete TypeScript coverage

**Frontend Components Status:**
- ✅ HeroSection - Animated landing page with feature showcase
- ✅ StockAnalysisForm - Symbol input with validation and popular stock suggestions (US + Japanese stocks)
- ✅ AnalysisResults - Complete 6-category analysis display with metrics and charts
- ✅ UI Components - Button, Input, Card, Progress, Badge with variants and accessibility
- ✅ Japanese Stock Support - Enhanced validation, popular Japanese stocks, bilingual error messages

### ✅ Latest Completed Features (2025-07-18)
1. **Japanese Stock Analysis Features** - Complete implementation
   - Frontend validation update: Regular expression `/^[A-Z0-9.-]{1,10}$/` supports Japanese stock format (NNNN.T)
   - Popular Japanese stocks added: Toyota (7203.T), Sony (6758.T), Honda (7267.T), Keyence (6861.T)
   - UI message improvement: "Enter US stock (AAPL) or Japanese stock (7203.T) symbol"
   - End-to-end test completed: Toyota (7203.T) 6-category analysis success confirmed
   - Backend compatibility confirmed: Japanese stock data retrieval and analysis via yfinance working properly

2. **Data Visualization Features** - Complete implementation
   - Recharts-based price chart implementation
   - Custom tooltips, volume bars, moving average display
   - Pattern charts, technical indicator charts, volatility charts
   - Chart container and data adapter functionality

### 🔄 In Progress
1. **Test Quality Improvement** - Improving test coverage and fixing syntax errors
2. **Business Logic Testing** - Implementing tests for main analysis modules

### 📋 Pending Implementation  
1. **Test Quality Improvement** - Improving test coverage (currently 9%)
2. **Production Ready Features** - Authentication, rate limiting, caching, monitoring
3. **Advanced ML Models** - Deep learning models, sentiment analysis, news integration
4. **Real-time Features** - WebSocket connections, live data streaming
5. **Testing Suite** - Frontend unit tests, integration tests, E2E testing

## Development Commands

### Backend (Python)
The backend uses uv as package manager. Current setup:

```bash
# In backend/ directory
# Project is already initialized with pyproject.toml

# Current dependencies (already installed):
# - Core: yfinance, pandas, numpy, scikit-learn, fastapi, pydantic
# - Technical analysis: matplotlib, seaborn, statsmodels  
# - Development: pytest, ruff, mypy, pytest-cov, pytest-asyncio

# Development commands:
uv run --frozen ruff format .      # Code formatting
uv run --frozen ruff check .       # Linting
uv run --frozen pytest             # Test execution (currently has syntax errors)
uv run --frozen mypy .             # Type checking
./start-dev.sh                     # Start development server
```

#### Current Test Status
- **Test Coverage**: 9% (159 of 1,833 lines tested)
- **Test Code**: Has syntax errors, needs fixing
- **Module Coverage**: Data models 68%, pattern analysis 29%, other modules 0%

### Frontend (Next.js + TypeScript)
The frontend uses bun as package manager:

```bash
# In frontend/ directory
bun install
bun dev

# Development commands
bun run format      # Format with biome
bun run lint        # Lint with biome  
bun run type-check  # TypeScript type checking
bun run build       # Build for production
```

## Project Structure

```
trendscope/
├── backend/          # Python backend with comprehensive 6-category analysis
│   ├── src/trendscope_backend/
│   │   ├── analysis/         # Analysis modules (technical, patterns, volatility, ML)
│   │   │   ├── technical/        # Technical indicators (SMA, EMA, RSI, MACD, etc.)
│   │   │   ├── patterns/         # Pattern recognition module
│   │   │   ├── volatility/       # Volatility analysis module
│   │   │   ├── ml/              # Machine learning predictions
│   │   │   ├── scoring/          # Integrated scoring system
│   │   │   └── fundamental/      # Fundamental analysis (placeholder)
│   │   ├── api/             # FastAPI endpoints and routing
│   │   │   ├── main.py          # FastAPI application setup
│   │   │   ├── analysis.py       # Technical analysis endpoints
│   │   │   ├── comprehensive_analysis.py  # Comprehensive analysis endpoints
│   │   │   └── historical_data.py  # Historical data endpoints
│   │   ├── data/            # Data models and stock data fetching
│   │   └── utils/           # Utility functions (config, logging, validation)
│   ├── tests/               # Test suite (9% coverage, needs improvement)
│   ├── pyproject.toml       # Python project configuration
│   ├── main.py             # Application entry point
│   ├── start-dev.sh        # Development server script
│   └── scripts/            # Utility scripts (batch_analysis.py)
├── frontend/         # Next.js frontend with TypeScript
│   ├── src/
│   │   ├── app/             # Next.js app directory (layout, page, providers)
│   │   ├── components/      # React components (UI, analysis, charts)
│   │   │   ├── charts/          # Chart components (price, pattern, volatility)
│   │   │   ├── analysis/        # Analysis result components
│   │   │   └── ui/              # UI components (button, card, input, etc.)
│   │   ├── hooks/           # Custom React hooks for API integration
│   │   ├── lib/             # Utilities (API client, error handling, utils)
│   │   └── types/           # TypeScript type definitions
│   ├── biome.json           # Code formatting and linting
│   ├── tailwind.config.js   # Tailwind CSS configuration
│   └── package.json         # Dependencies and scripts
├── compose.yaml      # Docker Compose configuration
├── DEVELOPMENT.md    # Development setup guide
└── CLAUDE.md        # Development progress and guidelines
```

## Analysis Methodology

### 6-Category Analysis Framework

1. **Technical Analysis**: Moving averages, RSI, MACD, Bollinger Bands
2. **Price Pattern Analysis**: Trend lines, candlestick patterns 
3. **Volatility Analysis**: Standard deviation, ATR, volatility ratios
4. **Machine Learning**: ARIMA/SARIMA, LSTM, Random Forest, SVM
5. **Fundamental Elements**: Volume analysis, sector/market correlations
6. **Integrated Scoring**: Weighted combination with confidence intervals

### Implementation Phases

- **Phase 1**: Basic technical indicators (SMA/EMA, RSI, MACD, Bollinger Bands) ✅
- **Phase 2**: Advanced analysis (pattern recognition, volatility, volume) ✅
- **Phase 3**: Machine learning integration and scoring system ✅
- **Phase 4**: Frontend implementation and deployment ✅
- **Phase 5**: Japanese stock market support ✅
- **Phase 6**: Data visualization and charts ✅
- **Phase 7**: Test quality improvement 🔄 (In Progress)

### API Endpoints

The backend provides the following analysis endpoints:

1. **`/health`** - Health check and service status
2. **`/api/v1/analysis/{symbol}`** - Technical analysis only
3. **`/api/v1/comprehensive/{symbol}`** - Full 6-category analysis
4. **`/api/v1/historical/{symbol}`** - Historical data with various time periods

#### Historical Data Endpoints
- **`/api/v1/historical/{symbol}/1d`** - 1-day historical data
- **`/api/v1/historical/{symbol}/5d`** - 5-day historical data
- **`/api/v1/historical/{symbol}/1mo`** - 1-month historical data
- **`/api/v1/historical/{symbol}/3mo`** - 3-month historical data
- **`/api/v1/historical/{symbol}/6mo`** - 6-month historical data
- **`/api/v1/historical/{symbol}/1y`** - 1-year historical data
- **`/api/v1/historical/{symbol}/2y`** - 2-year historical data
- **`/api/v1/historical/{symbol}/5y`** - 5-year historical data
- **`/api/v1/historical/{symbol}/10y`** - 10-year historical data
- **`/api/v1/historical/{symbol}/ytd`** - Year-to-date historical data
- **`/api/v1/historical/{symbol}/max`** - Maximum available historical data

## Key Implementation Requirements

### Backend Requirements
- Must use Python 3.12+ with comprehensive analysis libraries
- Must implement 6-category analysis framework
- Must provide probability-based predictions with confidence intervals
- Must integrate yfinance for stock data retrieval
- Must provide FastAPI endpoints for frontend communication

### Frontend Requirements
- Must use Next.js with TypeScript
- Must accept stock symbol input from users (US and Japanese markets)
- Must display analysis results with clear probability indicators
- Must show confidence levels and uncertainty measures
- Must integrate with backend API for real-time analysis
- Must support Japanese stock format validation (NNNN.T)

## Development Guidelines

### Code Quality
- Follow TDD principles with comprehensive test coverage
- Use type hints for all Python functions
- Use TypeScript strict mode for frontend
- Include comprehensive documentation with examples for all public functions

### Documentation Standards
- Python: Use detailed docstrings with Args, Returns, Raises, and Example sections
- TypeScript: Use JSDoc with @description, @param, @returns, @throws, and @example tags
- All business logic must include clear explanatory comments

### Testing
- Python: Use pytest with coverage reporting (`pytest --cov=src --cov-report=html`)
- TypeScript: Use bun test
- Must write tests for all new functionality

#### Current Test Status
- **Overall Coverage**: 9% (159/1,833 lines tested)
- **Module Coverage**: 
  - Data models: 68% (well-tested)
  - Pattern recognition: 29% (partially tested)
  - Technical indicators: 0% (not tested)
  - Volatility analysis: 0% (not tested)
  - ML predictions: 0% (not tested)
  - Integrated scoring: 0% (not tested)

#### Immediate Testing Priorities
1. Fix syntax errors in test files
2. Add comprehensive tests for technical indicators
3. Implement tests for volatility analysis
4. Add tests for ML prediction modules
5. Create integration tests for comprehensive analysis

## Security Notes
- Never hardcode API keys or credentials
- Always use environment variables for sensitive data
- Implement proper error handling for all API calls
- Validate all user inputs before processing