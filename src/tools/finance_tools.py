import yfinance as yf
from langchain_core.tools import tool

@tool
def get_stock_price(ticker: str) -> str:
    """Fetch the current stock price and key market data for a given ticker.

    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL', 'GOOGL', 'AMZN').

    Returns:
        Current price, 52-week high/low, and market capitalization.
    """

    stock = yf.Ticker(ticker)
    info = stock.info
    return (
        f"Ticker: {ticker}\n"
        f"Price: ${info.get('currentPrice', 'N/A')}\n"
        f"52-Week High: ${info.get('fiftyTwoWeekHigh', 'N/A')}\n"
        f"52-Week Low: ${info.get('fiftyTwoWeekLow', 'N/A')}\n"
        f"Market Cap: {info.get('marketCap', 'N/A')}"
    )

@tool
def get_market_trend(ticker: str, period: str = "1mo") -> str:
    """Fetch market trend data for a stock over a given time period.

    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL', 'TSLA', 'MSFT').
        period: Lookback period for trend analysis. Valid options: 1d, 5d, 1mo, 3mo, 6mo, 1y. Defaults to '1mo'.

    Returns:
        Price movement summary including start/end price, percentage change, and high/low for the period.
    """

    stock = yf.Ticker(ticker)
    hist = stock.history(period=period)
    if hist.empty:
        return f"No data found for {ticker}"
    start_price = hist['Close'].iloc[0]
    end_price = hist['Close'].iloc[-1]
    change_pct = ((end_price - start_price) / start_price) * 100
    
    return (
        f"Ticker: {ticker} | Period: {period}\n"
        f"Start: ${start_price:.2f} | End: ${end_price:.2f}\n"
        f"Change: {change_pct:.2f}%\n"
        f"High: ${hist['Close'].max():.2f} | Low: ${hist['Close'].min():.2f}"
    )

@tool
def build_portfolio(risk_level: str, investment_amount: float) -> str:
    """
        Build a diversified portfolio allocation based on the user's risk tolerance and total investment amount.

        Args:
            risk_level: User's risk tolerance - one of 'low', 'medium', or 'high'.
            investment_amount: Total dollar amount the user wants to invest.

        Returns:
            A breakdown of suggested asset allocations with dollar amounts for each position.
    """

    allocations = {
        "low": {"Bonds (BND)": 0.5, "S&P 500 (SPY)": 0.3, "Gold (GLD)": 0.2},
        "medium": {"S&P 500 (SPY)": 0.4, "Tech (QQQ)": 0.3, "Bonds (BND)": 0.2, "Gold (GLD)": 0.1},
        "high": {"Tech (QQQ)": 0.4, "S&P 500 (SPY)": 0.3, "Crypto (BITO)": 0.2, "Small Cap (IWM)": 0.1},
    }
    alloc = allocations.get(risk_level.lower(), allocations["medium"])
    result = f"Suggested Portfolio (Risk: {risk_level}, Amount: ${investment_amount:,.2f}):\n"
    for asset, pct in alloc.items():
        result += f"  {asset}: ${investment_amount * pct:,.2f} ({pct*100:.0f}%)\n"
    
    return result
