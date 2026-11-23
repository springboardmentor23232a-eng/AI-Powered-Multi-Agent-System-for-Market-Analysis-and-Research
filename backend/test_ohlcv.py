
import yfinance as yf

# Select a company
ticker = yf.Ticker("RELIANCE.NS")

# Retrieve 1 year of historical stock data
data = ticker.history(period="1y", interval="1d", auto_adjust=False)

# Extract OHLCV columns
ohlcv = data[["Open", "High", "Low", "Close", "Volume"]]

# Display the latest 10 records
print(ohlcv.tail(10))

# Display total records
print("\nTotal Records:", len(ohlcv))

# Check missing values
print("\nMissing Values:")
print(ohlcv.isnull().sum())


# Validate OHLCV data

print("\n--- DATA VALIDATION ---")

# 1. Check duplicate dates
print("Duplicate Dates:", data.index.duplicated().sum())

# 2. Check missing values
print("\nMissing Values:")
print(ohlcv.isnull().sum())

# 3. Check invalid price relationships
invalid_prices = (
    (ohlcv["High"] < ohlcv["Low"]) |
    (ohlcv["High"] < ohlcv[["Open", "Close"]].max(axis=1)) |
    (ohlcv["Low"] > ohlcv[["Open", "Close"]].min(axis=1))
)

print("\nInvalid Price Records:", invalid_prices.sum())

# 4. Check negative volume
print("Negative Volume Records:", (ohlcv["Volume"] < 0).sum())


# Display records with invalid price relationships
print("\nInvalid Price Details:")
print(ohlcv[invalid_prices])


# Create a cleaned OHLCV dataset
cleaned_ohlcv = ohlcv[~invalid_prices].copy()

print("\n--- CLEANED DATA ---")
print("Original Records:", len(ohlcv))
print("Cleaned Records:", len(cleaned_ohlcv))
print("Removed Records:", len(ohlcv) - len(cleaned_ohlcv))
