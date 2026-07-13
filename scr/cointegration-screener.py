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





