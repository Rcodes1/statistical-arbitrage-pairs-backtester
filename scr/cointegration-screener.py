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

def find_tradable_pairs(prices, threshold):
    """
    screens all asset combinations for cointegration and extracts pairs falling below p-value threshold
    """
    from statsmodels.tsa.stattools import coint
    tickers = prices.columns
    n = len(tickers)
    valid_pairs = []
    matrix = pd.DataFrame(index=tickers, columns=tickers)

    # fills diagonal with 1.0 (where asset is compared with it self)
    for ticker in tickers:
        matrix.loc[ticker,ticker] = 1.0

    #iterates through all but last asset
    for idx_A in range(n):
        #iterates only through assets after current asset
        for idx_B in range(idx_A + 1, n):
            ticker_A = tickers[idx_A]
            ticker_B = tickers[idx_B]
            
            #performs cointegration test
            _, p_value, _ = coint(prices[ticker_A], prices[ticker_B])
                
            #saves p-value into matrix symemtrically
            matrix.loc[[ticker_A, ticker_B] , [ticker_B, ticker_A]] = p_value
                
            if p_value < threshold:
                valid_pairs.append({
                    "Asset A": ticker_A,
                    "Asset B": ticker_B,
                    "P-Value": round(p_value,4)
                })
    return matrix , pd.DataFrame(valid_pairs)

if __name__ == "__main__":
    #loads configuration settings
    config = load_config()
    #pulls tickers from YAML config
    tickers = config["universe"]["tickers"]
    #pulls threshold from YAML config
    p_value_threshold = config["cointegration"]["p_value_threshold"]

    #downloads clean historical prices
    prices = download_market_data(tickers, config["data"]["start_date"], config["data"]["end_date"])

    #screens all asset combinations and extracts matches
    p_value_matrix, results = find_tradable_pairs(prices, threshold = p_value_threshold)
    
    #clears axis names
    p_value_matrix.index.name = None
    p_value_matrix.columns.name = None

    #output final results table
    if not results.empty:
        print(f"""\n=== Cointegration P-Value Matrix ===
\n{p_value_matrix.astype(float).round(4).to_string()} 
\n \n=== Significant Cointegration Pairs === 
\n{results.to_string(index=False)}""")
    else:
        print(f"No cointegration pairs found matching your criteria (p < {p_value_threshold}) \n {p_value_matrix}")



    







