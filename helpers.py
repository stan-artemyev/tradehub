import csv
from datetime import datetime, time, timedelta
import pytz
import requests
import urllib
import uuid
import yfinance as yf

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


def usd(value):
    """Format value as USD."""
    
    if value < 0:
        value = abs(value)
        return f"-${value:,.2f}"
    else:
        return f"${value:,.2f}"
    

def custom_humanize(number):
    """
    Convert a large number to a short version with K, M, B, T suffixes.
    
    Args:
    number (float): The number to convert.
    
    Returns:
    str: The converted number as a string with the appropriate suffix
    or an empty string if the argument is an empty string.
    """
    # Check if the number is empty
    if number == "":
        return ""
    else:        
        # Define suffixes for large numbers
        suffixes = ['', 'K', 'M', 'B', 'T']
        magnitude = 0
        
        # Loop to divide the number and increase the magnitude
        while abs(number) >= 1000 and magnitude < len(suffixes) - 1:
            magnitude += 1
            number /= 1000.0
        
        # Format the number with 2 decimal places and append the suffix
        return f"{number:.2f}{suffixes[magnitude]}"
    

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
        previous_close = round(float(quotes[-2]["Adj Close"]), 2)
        
        return {"price": price, "previous_close": previous_close, "symbol": symbol}
    except (KeyError, IndexError, requests.RequestException, ValueError):
        return None
        

def get_data(symbol):
    """Look up quote for symbol using yfinance."""
    
    # Capitalize symbol
    symbol = symbol.upper()
    
    # Fetch the real-time market data
    try:
        # Get the current price of the stock using lookup function
        current_price = usd(lookup(symbol).get("price", 0))
        
        # Create a Ticker object for the specified stock
        stock = yf.Ticker(symbol)
        
        # Get stock_info dictionary
        stock_info = stock.info
        
        # Get necessary market details data from stock_info dictionary    
        previous_close = usd(round(stock_info.get("previousClose", 0) , 2))
        open_price = usd(round(stock_info.get("open", 0), 2))
        day_high = usd(round(stock_info.get("dayHigh", 0), 2))
        day_low = usd(round(stock_info.get("dayLow", 0), 2))
        bid_price = usd(round(stock_info.get("bid", 0), 2))
        bid_size = stock_info.get("bidSize", "N/A")
        ask_price = usd(round(stock_info.get("ask", 0), 2))
        ask_size = stock_info.get("askSize", "N/A")
        volume = custom_humanize(stock_info.get("volume", 0))
        average_volume = custom_humanize(stock_info.get("averageVolume", 0))    
        market_cap = custom_humanize(stock_info.get("marketCap", 0))
        symbol_name = stock_info.get("longName", symbol)
                        
        # Look for dividend_yield in stock_info
        if "dividendYield" in stock_info:
            dividend_yield = f'{round(stock_info["dividendYield"] * 100, 2)}%'
        elif "yield" in stock_info:
            dividend_yield = f'{round(stock_info["yield"] * 100, 2)}%'
        else:
            dividend_yield = "-"
        
        # Look for PE in stock_info
        if "trailingPE" in stock_info:
            pe = round(stock_info["trailingPE"], 2)
        elif "forwardPE" in stock_info:
            pe = round(stock_info["forwardPE"], 2)
        else:
            pe = "-"
        
        fifty_two_week_high = usd(round(stock_info.get("fiftyTwoWeekHigh", "N/A"), 2))
        fifty_two_week_low = usd(round(stock_info["fiftyTwoWeekLow"], 2))
        currency = stock_info.get("currency", "USD")
        
        # Calculate price difference
        price_diff = round(float(current_price.replace("$", "")) - float(previous_close.replace("$", "")), 2)
        
        # Calculate percentage change
        percentage_change = round(price_diff / float(previous_close.replace("$", "")) * 100, 2)
        
        # Set price difference color and add "+" to price_diff and percentage_change if > 0
        if price_diff > 0:
            price_diff = f"+{price_diff}"
            percentage_change = f"+{percentage_change}"
            price_diff_color = "green"
        elif price_diff < 0:
            price_diff_color = "red"
        else:
            price_diff_color = ""
        
        # Get current time and format to HH:MM:SS
        current_time = datetime.now().strftime("%H:%M:%S")
        
        # Check if the market is open
        if market_is_open():
            market = "Open"
        else:
            market = "Closed"
        
        return {"price": current_price, "previous_close": previous_close, "open_price": open_price, "volume": volume,
                    "average_volume": average_volume, "market_cap": market_cap, "symbol_name": symbol_name, "dividend_yield": dividend_yield,
                    "pe": pe, "fifty_two_week_high": fifty_two_week_high, "fifty_two_week_low": fifty_two_week_low, "bid_price": bid_price,
                    "bid_size": bid_size, "ask_price": ask_price, "ask_size": ask_size, "day_high": day_high, "day_low": day_low, "currency": currency,
                    "current_time": current_time, "market": market, "symbol": symbol, "price_diff": price_diff, "price_diff_color": price_diff_color,
                    "percentage_change": percentage_change
                    }
    except (KeyError, IndexError, ValueError):
        return None
    



