import csv
from datetime import datetime, time, date, timedelta
import pytz
import requests
import urllib
import uuid
import yfinance as yf
import logging

from flask import redirect, render_template, request, session
from functools import wraps


def apology(message, code=400):
    """Render message as an apology to user."""

    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [
            ("-", "--"),
            (" ", "-"),
            ("_", "__"),
            ("?", "~q"),
            ("%", "~p"),
            ("#", "~h"),
            ("/", "~s"),
            ('"', "''"),
        ]:
            s = s.replace(old, new)
        return s

    return render_template("apology.html", top=code, bottom=escape(message)), code


def login_required(f):
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/latest/patterns/viewdecorators/
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)

    return decorated_function

def get_data(symbol):
    """Look up quote for symbol using yfinance."""
    
    # Prepare API request
    symbol = symbol.upper()
    
    # Fetch the real-time market data
    try:
        # Create a Ticker object for the specified stock
        stock = yf.Ticker(symbol)
        stock_info = stock.info
        
        # Get historical data for the stock from stock_info
        current_price = round(stock_info["currentPrice"], 2)
        previous_close = round(stock_info["previousClose"], 2)
        open_price = round(stock_info["open"], 2)
        day_high = round(stock_info["dayHigh"], 2)
        day_low = round(stock_info["dayLow"], 2)
        bid_price = round(stock_info["bid"], 2)
        bid_size = stock_info["bidSize"]
        ask_price = round(stock_info["ask"], 2)
        ask_size = stock_info["askSize"]
        volume = stock_info["volume"]
        average_volume = stock_info["averageVolume"]
        market_cap = stock_info["marketCap"]
        company_name = stock_info["longName"]
        dividend_yield = stock_info["dividendYield"]
        pe = stock_info["trailingPE"]
        fifty_two_week_high = round(stock_info["fiftyTwoWeekHigh"], 2)
        fifty_two_week_low = round(stock_info["fiftyTwoWeekLow"], 2)
        exchange = stock_info["exchange"]
        
        if not None in (current_price, previous_close, open_price, volume, 
                        average_volume, market_cap, company_name, dividend_yield, pe):
            return {"current_price": current_price, "previous_close": previous_close, "open_price": open_price, "volume": volume,
                    "average_volume": average_volume, "market_cap": market_cap, "company_name": company_name, "dividend_yield": dividend_yield,
                    "pe": pe, "fifty_two_week_high": fifty_two_week_high, "fifty_two_week_low": fifty_two_week_low, "bid_price": bid_price,
                    "bid_size": bid_size, "ask_price": ask_price, "ask_size": ask_size, "day_high": day_high, "day_low": day_low, "exchange": exchange
                    }
        else:
            logging.warning(f"Missing data for symbol: {symbol}")
            return None
    except yf.exceptions.YahooFinanceError as e:
        logging.error(f"Error fetching data for symbol: {symbol} - {e}")
        return None
    except (KeyError, IndexError, ValueError) as e:
        logging.warning(f"Error extracting data for symbol: {symbol} - {e}")
        return None


def lookup(symbol):
    """Look up quote for symbol."""

    # Prepare API request
    symbol = symbol.upper()
    end = datetime.now(pytz.timezone("US/Eastern"))
    start = end - timedelta(days=7)

    # Yahoo Finance API
    url = (
        f"https://query1.finance.yahoo.com/v7/finance/download/{urllib.parse.quote_plus(symbol)}"
        f"?period1={int(start.timestamp())}"
        f"&period2={int(end.timestamp())}"
        f"&interval=1d&events=history&includeAdjustedClose=true"
    )

    # Query API
    try:
        response = requests.get(
            url,
            cookies={"session": str(uuid.uuid4())},
            headers={"Accept": "*/*", "User-Agent": request.headers.get("User-Agent")},
        )
        response.raise_for_status()

        # CSV header: Date,Open,High,Low,Close,Adj Close,Volume
        quotes = list(csv.DictReader(response.content.decode("utf-8").splitlines()))
        price = round(float(quotes[-1]["Adj Close"]), 2)
        return {"price": price, "symbol": symbol}
    except (KeyError, IndexError, requests.RequestException, ValueError):
        return None


def usd(value):
    """Format value as USD."""
    return f"${value:,.2f}"

def custom_humanize(number):
    """
    Convert a large number to a short version with K, M, B, T suffixes.
    
    Args:
    number (float): The number to convert.
    
    Returns:
    str: The converted number as a string with the appropriate suffix.
    """
    # Define suffixes for large numbers
    suffixes = ['', 'K', 'M', 'B', 'T']
    magnitude = 0
    
    # Loop to divide the number and increase the magnitude
    while abs(number) >= 1000 and magnitude < len(suffixes) - 1:
        magnitude += 1
        number /= 1000.0
    
    # Format the number with 2 decimal places and append the suffix
    return f"{number:.2f}{suffixes[magnitude]}"


# Dictionary to map exchange codes to full names
exchange_names = {
    "NMS": "NASDAQ Stock Market",
    "NYQ": "New York Stock Exchange (NYSE)",
    "ASE": "NYSE American (formerly American Stock Exchange)",
    "BATS": "BATS Global Markets",
    "TOR": "Toronto Stock Exchange (TSX)",
    "LON": "London Stock Exchange (LSE)",
    "HKEX": "Hong Kong Stock Exchange",
    "TSE": "Tokyo Stock Exchange",
    "SHE": "Shenzhen Stock Exchange",
    "SGX": "Singapore Exchange",
    "ASX": "Australian Securities Exchange",
    "ICE": "Intercontinental Exchange",
    "FWB": "Frankfurt Stock Exchange",
    # Add more mappings as needed
}

def market_is_open():
    # Define NYSE regular trading hours
    nyse_open = time(9, 30)
    nyse_close = time(16, 0)
    
    # Define NYSE early closing hour (1:00 PM ET)
    nyse_early_close = time(13, 0)
    
    # Get the current time in Eastern Time (ET)
    eastern = pytz.timezone('US/Eastern')
    now = datetime.now(eastern)
    current_time = now.time()
    
    # List of NYSE holidays (sample)
    holidays = [
        datetime(2024, 1, 1),   # New Year's Day
        datetime(2024, 7, 4),   # Independence Day
        datetime(2024, 12, 25)  # Christmas Day
    ]
    
    # List of early closing days (sample)
    early_closings = [
        datetime(2024, 11, 29), # Day after Thanksgiving
        datetime(2024, 12, 24)  # Christmas Eve
    ]
    
    # Remove time part from current date for comparison
    today = now.date()
    
    # Check if today is a holiday
    if today in [holiday.date() for holiday in holidays]:
        return False
    
    # Check if today is a weekend
    if now.weekday() >= 5:  # Saturday is 5 and Sunday is 6
        return False
    
    # Check if today is an early closing day
    if today in [early_closing.date() for early_closing in early_closings]:
        if nyse_open <= current_time < nyse_early_close:
            return True
        else:
            return False
    
    # Check if current time is within regular trading hours
    if nyse_open <= current_time < nyse_close:
        return True
    else:
        return False