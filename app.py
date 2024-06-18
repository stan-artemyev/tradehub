import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, jsonify
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime
import yfinance as yf

from helpers import apology, login_required, lookup, usd, get_data

# Configure application
app = Flask(__name__)

# Enable template auto-reloading when there's a change in code
app.config["TEMPLATES_AUTO_RELOAD"] = True
# Disable caching for static files
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Define username variable and using context processor function to make it available to all tempaltes
@app.context_processor
def inject_username():
    if "user_id" in session:
        user_id = session["user_id"]
        username = db.execute("SELECT username FROM users WHERE id = ?", user_id)[0]["username"]
        return {"username": username}
    else:
        return {"username": None}


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""

    stocks = db.execute(
        "SELECT symbol, symbol_name, SUM(amount) AS sum, AVG(price) AS average_price FROM stocks WHERE user_id = ? GROUP BY symbol HAVING sum > 0", session["user_id"]
    )

    # Get current prices of each stock that the user has and calculate their total
    total = 0 # initialize total
    total_performance = 0 # initialize total_performance

    for stock in stocks:
        # Get real-time stock price
        stock_info = lookup(stock["symbol"])
        stock["price"] = stock_info["price"] 
        
        # Calculate today's price percentage difference
        stock["previous_close"] = stock_info["previous_close"]
        stock["percentage_change"] = round((
            (stock["price"] - stock["previous_close"]) / stock["previous_close"]
        ) * 100, 2)
        
        # Calculate total current stock value
        stock["total"] = stock["sum"] * stock["price"]
        total += stock["total"]
        
        # Calculate performance and performance percentage
        total_investment = stock["sum"] * stock["average_price"]
        stock["performance"] = stock["total"] - total_investment
        stock["performance_percentage"] = round(stock["performance"] / total_investment * 100, 2)
        
        total_performance += stock["performance"]
        
    # Calculate total performance percentage change
    total_performance_percentage = round(total_performance / total * 100, 2)

    # Query cash from DB
    user_cash = db.execute("SELECT cash FROM users WHERE id = ?", session["user_id"])[0]["cash"]

    # Calculate TOTAL (stock values + user cash)
    total = total + user_cash

    return render_template(
        "index.html", stocks=stocks, cash=user_cash, total=total, total_performance=total_performance, total_performance_percentage=total_performance_percentage
    )


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""

    # User reached route via GET
    if request.method == "GET":
        # Query cash from DB
        user_cash = db.execute("SELECT cash FROM users WHERE id = ?", session["user_id"])[0]["cash"]
        
        return render_template("buy.html", user_cash=user_cash)

    # User reached route via POST (by submiting a buy button)
    else:
        symbol = request.form.get("symbol")
        shares = request.form.get("shares")

        # Ensure symbol was submitted
        if not symbol:
            return apology("must provide ticker symbol", 400)

        # Ensure provided symbol is correct
        elif lookup(symbol) == None:
            return apology("invalid symbol")

        # Ensure amount of share are provided
        elif not shares:
            return apology("must provide shares", 400)

        # Ensure amount of shares is integer and non-negative
        try:
            shares = int(shares)
            if shares < 1:
                return apology("negative shares", 400)
        except ValueError:
            return apology("non-integer shares", 400)

        # Check if the user has enough cash
        price = lookup(symbol)["price"]
        total = price * shares
        cash_query = db.execute(
            "SELECT cash FROM users WHERE id = ?", session["user_id"]
        )
        if cash_query:
            user_cash = cash_query[0]["cash"]
        else:
            return apology("no cash in DB")

        if total > user_cash:
            return apology("not enough cash")

        else:
            # Get current date/time and convert to SQL format YYYY-MM-DD HH:MM:SS
            date_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Get stock name
            symbol_name = get_data(symbol)["symbol_name"]

            # Buy stocks
            db.execute(
                "INSERT INTO stocks (symbol, symbol_name, price, amount, date_time, user_id) VALUES (?, ?, ?, ?, ?, ?)",
                symbol.upper(),
                symbol_name,
                price,
                shares,
                date_time,
                session["user_id"],
            )

            # Correct cash after purchase in DB
            user_cash = user_cash - total
            db.execute(
                "UPDATE users SET cash = ? WHERE id = ?", user_cash, session["user_id"]
            )

        # Alert the user
        flash("Bought!")

        # Redirect the user to the home page
        return redirect("/")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""

    # Query transactions history from stocks table
    stocks = db.execute(
        "SELECT symbol, symbol_name, price, amount, date_time FROM stocks WHERE user_id = ?",
        session["user_id"],
    )

    return render_template("history.html", stocks=stocks)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(
            rows[0]["hash"], request.form.get("password")
        ):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]
        
        # Assign the username to the global variable
        global username
        username = request.form.get("username")

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""

    # User reached route via POST (by AJAX request from refreshQuote)
    if request.method == "POST":
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            try:
                # Log headers and JSON payload
                print("Headers:", request.headers)
                print("Request data:", request.get_data())

                # Get the symbol from the AJAX request
                symbol = request.get_json()["symbol"]
                if not symbol:
                    return jsonify({"error": "Invalid symbol"}), 400

                # Call the get_data() function to get the updated stock data
                stock_data = get_data(symbol)
                
                if stock_data is None:
                    return jsonify({"error": "Failed to fetch stock data"}), 500

                return jsonify(stock_data)
            except Exception as e:
                print(f"Error processing request: {e}")  # Log the error
                return jsonify({"error": "An error occurred while processing the request"}), 500
    
        # User reached route via GET (by clicking a quote button)
        else:     
            symbol = request.form.get("symbol")

            # Ensure symbol was submitted
            if not symbol:
                return apology("must provide ticker symbol")
            
            # Ensure provided symbol is correct
            elif lookup(symbol) == None:
                return apology("invalid symbol")
            
            # Call the get_data() function to get stock data    
            stock_data = get_data(symbol)
            
            # Query cash from DB
            user_cash = db.execute("SELECT cash FROM users WHERE id = ?", session["user_id"])[0]["cash"]
            
            # Query available shares from DB for a current logged in user
            available_shares = db.execute("SELECT SUM(amount) AS sum FROM stocks WHERE user_id = ? AND symbol = ?", session["user_id"], symbol.upper())[0]["sum"]
            
            return render_template("quoted.html", stock_data=stock_data, user_cash=user_cash, available_shares=available_shares)

    # User reached route via GET
    else:
        return render_template("quote.html")        

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        # Ensure username was submitted
        if not username:
            return apology("must provide username", 400)

        # Ensure password was submitted
        elif not password:
            return apology("must provide password", 400)

        # Ensure passwords are identical
        elif password != confirmation:
            return apology("passwords don't match", 400)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", username)

        # Ensure username is unique
        if len(rows) > 0:
            return apology(f"The username: {username} was taken", 400)

        # Add new user to DB
        db.execute(
            "INSERT INTO users (username, hash) VALUES (?, ?);",
            username,
            generate_password_hash(password),
        )

        # Log user in immediately after registration
        rows = db.execute("SELECT * FROM users WHERE username = ?", username)
        session["user_id"] = rows[0]["id"]

        # Alert the user
        flash("You have successfully registered!")

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""

    # Query stocks from DB for a current logged in user
    stocks = db.execute(
        "SELECT symbol, SUM(amount) AS sum FROM stocks WHERE user_id = ? GROUP BY symbol HAVING sum > 0",
        session["user_id"],
    )

    # Display the page if the User reached route via GET
    if request.method == "GET":
        return render_template("sell.html", stocks=stocks)

    # User reached route via POST (as by submitting a form via POST)
    else:
        # Check if the user submitted correct amount of shares
        symbol = request.form.get("symbol")
        shares = request.form.get("shares")

        if not symbol:
            return apology("must provide ticker symbol", 400)

        if not shares:
            return apology("must provide shares", 400)

        # Get amount of shares that the user has for a selected symbol
        user_shares = 0

        for stock in stocks:
            if stock["symbol"] == symbol:
                user_shares = stock["sum"]
                break

        # Ensure amount of shares is > 1 and user has enough
        if int(shares) < 1 or int(shares) > user_shares:
            return apology("invalid shares", 400)

        else:
            # Get user's cash value
            cash = db.execute(
                "SELECT cash FROM users WHERE id = ?", session["user_id"]
            )[0]["cash"]

            # Get current stock price and total value
            price = lookup(symbol)["price"]
            total = price * int(shares)
            
            # Get stock name
            symbol_name = get_data(symbol)["symbol_name"]

            # Sell shares and update DB with negative amount of shares and updated cash value
            date_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            db.execute(
                "INSERT INTO stocks (symbol, symbol_name, price, amount, date_time, user_id) VALUES (?, ?, ?, ?, ?, ?);",
                symbol.upper(),
                symbol_name,
                price,
                -int(shares),
                date_time,
                session["user_id"],
            )

            cash = cash + total
            db.execute(
                "UPDATE users SET cash = ? WHERE id = ?", cash, session["user_id"]
            )

            # Alert the user
            flash("Sold!")

            # Redirect the user to the home page
            return redirect("/")


@app.route("/change_password", methods=["GET", "POST"])
def change_password():
    """Change user's password"""

    # User reached route via GET (as by clicking a change password link)
    if request.method == "GET":
        return render_template("change_password.html")

    # User reached route via POST (as by submitting a form via POST)
    else:
        username = request.form.get("username")
        password = request.form.get("password")
        new_password = request.form.get("new_password")
        new_password_confirmation = request.form.get("new_password_confirmation")

        # Ensure username was submitted
        if not username:
            return apology("must provide username", 400)

        # Ensure password was submitted
        elif not password or not new_password or not new_password_confirmation:
            return apology("must provide password", 400)

        # Ensure passwords are identical
        elif new_password != new_password_confirmation:
            return apology("passwords don't match", 400)

        # Query database for username
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], password):
            return apology("invalid username and/or password", 403)

        # Update user's password
        db.execute(
            "UPDATE users SET hash = ? WHERE id = ?",
            generate_password_hash(password),
            session["user_id"],
        )

        # Alert the user
        flash("You have successfully changed your password")

        # Redirect user to home page
        return redirect("/")

@app.route("/money", methods=["GET", "POST"])
@login_required
def money():
    """Deposit/Withdray funds"""
    # User reached route via GET (as by clicking a link or via redirect)
    if request.method == "GET":
        # Query user's cash balance
        user_cash = db.execute("SELECT cash FROM users WHERE id = ?", session["user_id"])[0]["cash"]
        return render_template("money.html", user_cash=user_cash)

    # User reached route via POST (as by submitting a form via POST)
    else:
        # Get data from the moneyForm
        amount = request.form.get("amount")
        action = request.form.get("action")

        # Ensure amount was submitted
        if not amount:
            return apology("must provide amount", 400)
        elif float(amount) <= 0:
            return apology("amount must be greater than 0", 400)

        # Ensure action was submitted
        elif not action:
            return apology("must provide action", 400)

        # Get user's cash value
        user_cash = db.execute("SELECT cash FROM users WHERE id = ?", session["user_id"])[0]["cash"]

        # Deposit
        if action == "deposit":
            cash = user_cash + float(amount)
            db.execute("UPDATE users SET cash = ? WHERE id = ?", cash, session["user_id"])
            flash(f"${amount} was deposited!")
            return redirect("/")
        # Withdraw
        elif action == "withdraw":
            if float(amount) > user_cash:
                return apology("insufficient funds", 400)
            cash = user_cash - float(amount)
            db.execute("UPDATE users SET cash = ? WHERE id = ?", cash, session["user_id"])
            flash(f"${amount} was withdrawn")
            return redirect("/")
        else:
            return apology("invalid action", 400)
        

