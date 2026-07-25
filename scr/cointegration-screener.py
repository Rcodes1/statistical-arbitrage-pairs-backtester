import os
import yaml
import yfinance as yf
import pandas as pd

# finds the folder where this script is currently
script_dir = os.path.dirname(__file__)

# goes up one level and grabs config file
config_path = os.path.join(script_dir,"..","config.yaml")

def load_config(path = config_path):
    """
    loads the tickers and parameters from config.yaml wihtout path issues
    """
    with open(path, "r") as file:
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
                    "Asset_A": ticker_A,
                    "Asset_B": ticker_B,
                    "P-Value": round(p_value,4)
                })
    return matrix , pd.DataFrame(valid_pairs)

if __name__ == "__main__":
    config = load_config()
    tickers = config["universe"]["tickers"]
    p_value_threshold = config["cointegration"]["p_value_threshold"]
    prices = download_market_data(tickers, config["data"]["start_date"], config["data"]["end_date"])

    p_value_matrix, results = find_tradable_pairs(prices, threshold = p_value_threshold)
    
    p_value_matrix.index.name = None
    p_value_matrix.columns.name = None

    output_dir = os.path.join(script_dir,"..", "data")
    os.makedirs(output_dir, exist_ok=True)

    prices.to_csv(os.path.join(output_dir,"historical_prices.csv"))

    #output final results table
    if not results.empty:
        #sorts pairs so lowest p-value is at Row 0 
        results = results.sort_values(by="P-Value", ascending=True)

        results.to_csv(os.path.join(output_dir, "top_cointegrated_pairs.csv"), index=False)
        
        print(f"\n COINTEGRATION P-VALUE MATRIX \n{p_value_matrix.astype(float).round(4)}")

        print(f"\n SIGNIFICANT COINTEGRATION PAIRS \n{results.to_string(index=False)}")
    else:
        print(f"No cointegration pairs found matching your criteria (p < {p_value_threshold}) \n {p_value_matrix}")
