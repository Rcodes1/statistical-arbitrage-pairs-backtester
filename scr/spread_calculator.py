import os
import yaml
import pandas as pd
import statsmodels.api as sm
import matplotlib as plt

# finds the folder where this script is currently
script_dir = os.path.dirname(__file__)

# goes up one level and grabs config file
config_path = os.path.join(script_dir,'..','config.yaml')

def load_config(path = config_path):
    """
    loads values from config file
    """
    with open(path, 'r') as file:
        return yaml.safe_load(file)
    
def calculate_hedge_ratio(series_A, series_B):
    """
    Calculates the hedge ratio (beta) between two price series using the OLS regression.

    Parameters:
    series_A (pd.Series): The dependent asset prices (Y)
    series_B (pd.Series): The independent asset prices (X)

    Returns:
    float: The hedge ratio (gradient / beta coefficient of the regression)
    """
    Y = series_A
    #Adds a constant column to the independent variable (stock B)
    X = sm.add_constant(series_B)
    
    # Sets up OLS model (Y first, X second) and fit it
    model_fit = sm.OLS(Y, X).fit()

    #extracting gradient
    beta = model_fit.params[1]
    return beta

def calculate_spread(series_A, series_B, hedge_ratio):
    """
    Calculates the price spread between the two cointegration assets

    Parameters:
    series_A (p.d Series): Price series of asset A (Y)
    series_B (p.d Series): Price series of asset B (X)
    hedge_ratio (float): beta coefficient calculated from regression
    
    Returns:
    Pandas series: Resulting spread series
    """
    spread = series_A - (hedge_ratio * series_B)
    return spread

def calculate_rolling_zscore(spread):
    """
    Calculates rolling z-score of spread, to prevent look ahead bias

    Parameters:
    spread (ps.series): calculated price spread
    window (int): look back window loaded from YAML file

    Returns:
    pd.series: rolling z-score series
    """
    window = config["zscore"]["lookback_window"]

    rolling_mean = spread.rolling(window=window).mean()
    rolling_std = spread.rolling(window=window).std()
    z_scores = (spread - rolling_mean) / rolling_std
    return z_scores

def generate_signals(z_scores):
    """
    Generates trading signals based on z-score thresholds

    parameters:
    z_scores (pd.series): rolling z-score of the spread
    entry_threshold (float): z-score level to trigger an entry
    exit_threshold (float): z-score level to trigger a close

    Returns:
    ps.series: serires of signal flags matching input index:
                -1 = long the spread (buy asset A, short asset B)
                 1 = short the spread (short asset A, buy asset B)
                 0 = neutral (no position)
    """
    signals = []
    current_position = 0
    entry_threshold, exit_threshold = config["zscore"]["entry_threshold"], config["zscore"]["exit_threshold"]

    for z in z_scores:
        #handling warm up window where z-scores are NaN
        if pd.isna(z):
            signals.append(0)
            continue
        
        #look to enter a trade
        if current_position == 0:
            #look to enter a trade
            if z >  entry_threshold:
                current_position = 1
            elif z < -entry_threshold:
                current_position = -1

        #look to exit a short position    
        elif current_position == 1:
            if z <= exit_threshold:
                current_position = 0

        #look to exit a long position    
        elif current_position == -1:
            if z >= -exit_threshold:
                current_position = 0
            
        signals.append (current_position)

    return pd.Series(signals, index = z_scores.index, name = 'signal')

