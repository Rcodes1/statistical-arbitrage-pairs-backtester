import os
import yaml
import yfinance as yf
import pandas as pd

# finds the folder where this script is currently
script_dir = os.path.dirname(__file__)

# goes up one level and grabs config file
config_path = os.path.join(script_dir,'..','config.yaml')

def load_config(path = config_path):
    """
    loads the tickers and parameters from config.yaml wihtout path issues
    """
    with open(path, 'r') as file:
        return yaml.safe_load(file)
    
def download_market_data(tickers, start_date, end_date):
    """
    pulls historical prices from yfinance and cleans up missing data
    """
    raw_data = yf.download(tickers, start = start_date, end = end_date, progress = False)
    return raw_data["Close"].dropna()

def run_cointegration_screen(prices):
    """
    runs nested loop to test all pairs and returns symmetrical p-value matrix
    """
    from statsmodels.tsa.stattools import coint

    #grabs list of stock names from table headers
    tickers = prices.columns 

    #creates empty matrix with tickers as both the rows and columns
    matrix = pd.DataFrame(index=tickers, columns=tickers)

    #loops through every stock (rows)
    for ticker_A in tickers:
        #loops through every stock (columns)
        for ticker_B in tickers:

            #if stock compared to itself, p=1.0
            if ticker_A == ticker_B:
                matrix.loc[ticker_A, ticker_B] = 1.0
            else:
                # runs statistical test and uses just p-value
                _, p_value, _ = coint(prices[ticker_A], prices[ticker_B])

                #saves calculated p-value into matching cell of grid
                matrix.loc[ticker_A, ticker_B] = p_value
    return matrix

def find_tradable_pairs(matrix, threshold):
    """
    scans p-value matrix and extracts unique pairs that fall below threshold
    """
    tickers = matrix.columns
    valid_pairs =[]

    #loops through every cell in the matrix
    for ticker_A in tickers:
        for ticker_B in tickers: 

            #pulls calculated p-value for specific cell
            p_val = matrix.loc[ticker_A, ticker_B]

            if p_val < threshold:
                valid_pairs.append({
                    "Asset A": ticker_A,
                    "Asset B": ticker_B,
                    "P-Value": round(p_val, 4)
                })
    #converts list of saved dictionaries into clean pandas Data Frame
    return pd.DataFrame(valid_pairs)

if __name__ == "__main__":
    #loads configuration settings
    config = load_config()
    tickers = config["universe"]["tickers"]
    p_value_threshold = config.get("p_value_threshold", 0.05)

    #downloads clean historical prices
    prices = download_market_data(tickers, config["data"]["start_date"], config["data"]["end_date"])

    #screens all asset combinations and extracts matches
    p_value_matrix = run_cointegration_screen(prices)
    results = find_tradable_pairs(p_value_matrix, threshold=p_value_threshold)

    #output final results table
    if not results.empty:
        print(results.to_string(index = False))
    else:
        print("No cointegration pairs found matching your criteria.")



    







