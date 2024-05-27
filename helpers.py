import csv
import datetime
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
    
    # Get current date and time in US/Eastern timezone
    est = pytz.timezone("US/Eastern")
    current_time = datetime.datetime.now(est)

    # Check if the market is currently open (betwen 9AM and 4PM EST)
    market_is_open = (current_time.hour >= 9 and current_time.hour < 16)

    # Fetch the real-time market data
    try:
        # Create a Ticker object for the specified stock
        stock = yf.Ticker(symbol)
        stock_info = stock.info
        
        # Get historical data for the stock from stock_info
        current_price = round(stock_info["currentPrice"], 2)
        previous_close = round(stock_info["previousClose"], 2)
        open_price = round(stock_info["open"], 2)
        volume = stock_info["volume"]
        average_volume = stock_info["averageVolume"]
        market_cap = stock_info["marketCap"]
        company_name = stock_info["longName"]
        dividend_yield = stock_info["dividendYield"]
        pe = stock_info["trailingPE"]
        
        if not None in (current_price, previous_close, open_price, volume, 
                        average_volume, market_cap, company_name, dividend_yield, pe):
            return {"current_price": current_price, "previous_close": previous_close, "open_price": open_price, "volume": volume,
                    "average_volume": average_volume, "market_cap": market_cap, "company_name": company_name, "dividend_yield": dividend_yield, "pe": pe}
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
    end = datetime.datetime.now(pytz.timezone("US/Eastern"))
    start = end - datetime.timedelta(days=7)

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
