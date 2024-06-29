# TradeHub
## [TradeHub Demo](https://youtu.be/izLADZelsKo)
## Description
TradeHub is my CS50 final project. It's an interactive stock trading simulator designed to provide users with a realistic stock market experience. Users can create accounts, simulate buying and selling stocks using real-time data, manage their finances, and track their portfolio performance — all without financial risk. This project is a web application that uses a combination of frontend and backend technologies to deliver a seamless user experience.

- [TradeHub](#tradehub)
	- [TradeHub Demo](#tradehub-demo)
	- [Description](#description)
	- [Technologies Used](#technologies-used)
		- [Frontend](#frontend)
		- [Backend](#backend)
	- [File Descriptions](#file-descriptions)
		- [Frontend Files](#frontend-files)
		- [Backend Files](#backend-files)
		- [Database](#database)
	- [Design Choices](#design-choices)
		- [Security](#security)
		- [Real-Time Data Updates](#real-time-data-updates)
		- [Logo and User Interface](#logo-and-user-interface)
		- [Dynamic Content](#dynamic-content)
	- [Sections Description](#sections-description)
	- [Conclusion](#conclusion)


## Technologies Used

### Frontend

- **HTML**: For structuring the web pages.
- **CSS** & **Bootstrap** 5.3.3: For styling and responsive design.
- **JavaScript**: For dynamic content and interactivity.

### Backend

 - **Flask**: A lightweight WSGI web application framework in Python.
 - **Python**: The core programming language used for backend development.
 - **SQLite3**: SQL database using SQL module from CS50 library for storing user information, stock data and transaction history.
 - **Yahoo Finance API** & **yfinance** library: For fetching real-time stock data.
 - **werkzeug.security** module: For hashing passwords.
 - **flask_session** module: For managing user sessions.

## File Descriptions

### Frontend Files

- layout.html: The base HTML template used by other HTML files to maintain a consistent structure and styling across the site.
- index.html: The main page users see upon logging in. It displays the user’s portfolio, including the currently possessed stocks, their values, and performance. It also allows quick trading of stocks.
- register.html: Responsible for registering new users. Once registered, users are given an initial $10,000 in cash.
- quote.html: A page where users input stock symbols to get a quote.
- quoted.html: Displays a comprehensive response for the stock quote requested by the user.
- buy.html: A dedicated page for purchasing stocks. Users can enter the ticker symbol and the number of shares they wish to buy.
- sell.html: Similar to the buy page but for selling stocks. Users choose the ticker symbol and the number of shares they wish to sell.
- history.html: Displays a comprehensive log of all user transactions, enabling users to track their trading activities.
- money.html: Allows users to deposit or withdraw money.
- change_password.html: Allows users to change their passwords.
- apology.html: Handles edge cases such as incorrect passwords, invalid ticker symbols, incorrect amounts of shares, and other errors.
- refreshQuote.js: A JavaScript file that handles the update button on the quote page. It sends an AJAX request to the backend and updates the current price and market details without refreshing the entire page, enhancing user experience.
- sell.js: Updates the number of available shares based on the user’s selection.
- tradeForm.js: Includes a function that sets the action in a tradeForm based on the Buy/Sell button clicked and submits the form.
- index.js: Includes a function that gets values (amount of shares and symbol) from a form and passes them to the /buy or /sell route.
- styles.css: Contains custom CSS styles for the application.

### Backend Files

- app.py: The main Flask application file. It includes route definitions, database interactions, and integration with the frontend.
- helpers.py: Contains auxiliary functions:
  - apology: Renders a message as an apology to the user when something is not right.
  - login_required: Decorates routes to require login.
  - lookup: Looks up a stock for the current price and previous close price.
  - usd: Formats currency to USD format. E.g. $10.25
  - get_data: Fetches market details of a stock using yfinance.
  - custom_humanize: Converts large numbers to short versions with K, M, B, T suffixes.
  - market_is_open: Checks if the market is open.

### Database

- SQLite3 Database: Stores user information, stock data, and transaction history. The tradehub.db database includes two tables:
  * users: Stores user information such as usernames, hashed passwords, and cash balance.
  * stocks: Stores stock information and transaction history, including stock symbols and names, number of shares, the price at which the shares were bought or sold, and transaction date.



## Design Choices

### Security

One of the critical aspects of this project is security. I chose to use werkzeug.security to hash passwords instead of storing them in plaintext as it was implemented in CS50 Finance problem. This ensures that user credentials are stored securely, reducing the risk of unauthorized access. Additionally, I used flask_session to track logged-in users, providing a robust session management mechanism.

### Real-Time Data Updates

To enhance the user experience, I implemented a feature to update stock prices and market details without refreshing the entire page. For this, I wrote refreshQuote.js, which sends an AJAX request to the backend and returns a JSON response. This allows the application to update the current price and other details dynamically, providing users with up-to-date information.

### Logo and User Interface

To give TradeHub a unique identity, I used Google Gemini to generate a logo featuring the letter “T,” which I incorporated into the navigation bar. This adds a professional touch to the application.

### Dynamic Content

On the index page, I utilized Jinja syntax to loop through the database and create a dynamic table displaying the user’s currently possessed stocks. This ensures that the portfolio is always up-to-date and accurately reflects the user’s holdings.

## Sections Description

1. Login or Create an Account: Upon opening the app, users are greeted with a login screen. If they don’t have an account, they can easily create a new one.
2.	Index Page - Your Portfolio: The index page serves as the user’s portfolio, displaying all currently possessed stocks, their values, and performance. Users can quickly trade stocks from this page.
3.	Quote Page: The quote page allows users to look up stock prices using ticker symbols. It displays the current price and relevant market details and allows users to buy and sell stocks.
4.	Buy Section: Users can purchase stocks by entering the ticker symbol and the number of shares they wish to buy.
5.	Sell Section: Users can sell stocks by choosing the ticker symbol and the number of shares they wish to sell.
6.	History: The history section provides a comprehensive log of all user transactions, enabling users to track their trading activities.
7.	Account Menu: Accessible via the navigation bar, users can manage their finances by depositing or withdrawing money (money.html) and changing their passwords (change_password.html).

## Conclusion

TradeHub is a comprehensive stock trading simulator that combines robust frontend and backend technologies to deliver an exceptional user experience. By focusing on security, real-time data updates, and dynamic content, TradeHub provides users with a realistic and engaging stock market simulation. Thank you for exploring TradeHub. Happy trading! 😊