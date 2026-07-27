import os
import yaml
import pandas as pd
import statsmodels.api as sm
import matplotlib.pyplot as plt

# finds the folder where this script is currently
script_dir = os.path.dirname(__file__)

# goes up one level and grabs config file
config_path = os.path.join(script_dir,'..','config.yaml')

def load_config(path = config_path):
    """
    loads configuration settings from config.yaml
    """
    with open(path, 'r') as file:
        return yaml.safe_load(file)
    
def calculate_hedge_ratio(series_A, series_B):
    """
    calculates the hedge ratio (beta) between two price series using OLS regression
    """
    Y = series_A
    #Adds a constant column to the independent variable (stock B)
    X = sm.add_constant(series_B)
    
    # Sets up OLS model (Y first, X second) and fit it
    model_fit = sm.OLS(Y, X).fit()

    #extracting gradient
    beta = model_fit.params.iloc[1]
    return beta

def calculate_spread(series_A, series_B, hedge_ratio):
    """
    calculates the price spread between two cointegration assets
    """
    spread = series_A - (hedge_ratio * series_B)
    return spread

def calculate_rolling_zscore(spread):
    """
    calculates the rolling z-score of the spread to prevent lookahead bias
    """
    config = load_config()
    window = config["zscore"]["lookback_window"]

    rolling_mean = spread.rolling(window=window).mean()
    rolling_std = spread.rolling(window=window).std()
    z_scores = (spread - rolling_mean) / rolling_std
    return z_scores

def generate_signals(z_scores):
    """
    generates trading signals based on z score entry and exit thresholds

    Returns:
        pd.Series: signal flags matching the input index:
             1 = long the spread (buy asset A, short asset B)
             -1 = short the spread (short asset A, buy asset B)
             0 = neutral (no position)
    """
    config = load_config()
    signals = []
    current_position = 0
    entry_threshold = config["zscore"]["entry_threshold"]
    exit_threshold = config["zscore"]["exit_threshold"]

    for z in z_scores:
        #handling warm up window where z-scores are NaN
        if pd.isna(z):
            signals.append(0)
            continue
        
        #look to enter a trade
        if current_position == 0:
            #look to enter a trade
            if z >  entry_threshold:
                current_position = -1
            elif z < -entry_threshold:
                current_position = 1

        #look to exit a short position    
        elif current_position == -1:
            if z <= exit_threshold:
                current_position = 0

        #look to exit a long position    
        elif current_position == 1:
            if z >= -exit_threshold:
                current_position = 0
            
        signals.append (current_position)

    return pd.Series(signals, index = z_scores.index, name = 'signal')

def plot_signals (df, save_path = "pairs_trading_backtest.png"):
    """
    plots asset prices, spread and rolling z-scores with active signal shading
    """
    config = load_config()
    entry_threshold = config["zscore"]["entry_threshold"]
    exit_threshold = config["zscore"]["exit_threshold"]

    fig, (ax1, ax2) = plt.subplots(2,1, figsize=(12,10), sharex = True)

    #PANEL 1 - asset prices and spread
    ax1.plot(df.index, df["Asset_A"], label="Asset A", color="blue", alpha=0.75, linewidth=1.2)
    ax1.plot(df.index, df["Asset_B"], label="Asset B", color="orange", alpha=0.75, linewidth=1.2)
    ax1.plot(df.index, df["spread"], label="Spread (A - beta * B)", color="gray", linewidth=1.5)

    ax1.set_title("Asset prices and calculated spread", fontsize=14, fontweight="bold", color="black")
    ax1.set_ylabel("price / value", fontsize=12)
    ax1.legend(loc="upper left", frameon=True,  facecolor="white", edgecolor="none")
    ax1.grid(True, linestyle="--", alpha=0.4, color="lightgrey")

    #PANEL 2 - rolling z score and thresholds
    ax2.plot(df["z_score"], label="Rolling z-score", color="black", linewidth=1.2)
    ax2.axhline(entry_threshold, color="red", linestyle="--", linewidth=1.2, label=f"Upper Entry ({entry_threshold})")
    ax2.axhline(-entry_threshold, color="red", linestyle="--", linewidth=1.2, label=f"Lower Entry (-{entry_threshold})")
    ax2.axhline(exit_threshold, color="green", linestyle=":", linewidth=1.2, label=f"Exit Threshold ({exit_threshold})")
    if exit_threshold != 0:
        ax2.axhline(-exit_threshold, color='green', linestyle=':', linewidth=1.2)
        
    ax2.fill_between(df.index, df["z_score"], where=(df["signal"] == 1), 
                     color="green", alpha=0.15, label="Long Spread (Buy A, Short B)")
    ax2.fill_between(df.index, df["z_score"], where=(df["signal"] == -1), 
                     color="red", alpha=0.15, label="Short Spread (Short A, Buy B)")
    
    ax2.set_title("Rolling Z-Score with Strategy Thresholds & Position Shading", fontsize=14, fontweight="bold", color="black")
    ax2.set_ylabel("Z-Score Standard Deviations", fontsize=12)
    ax2.set_xlabel("Date", fontsize=12)
    ax2.legend(loc="upper left", frameon=True, facecolor="white", edgecolor="none")
    ax2.grid(True, linestyle="--", alpha=0.4, color="lightgray")
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=300)
    print(f"Backtest chart rendered and saved to {save_path}")
    plt.show()

if __name__ == '__main__':
    config = load_config()
    
    historical_data_path = os.path.join(script_dir, '..', 'data', 'historical_prices.csv')
    pairs_summary_path = os.path.join(script_dir, '..', 'data', 'top_cointegrated_pairs.csv')
    
    try:
        #loads best pair from section 2
        price_df = pd.read_csv(historical_data_path, index_col=0, parse_dates=True)
        pairs_df = pd.read_csv(pairs_summary_path)
        
        ticker_A = pairs_df.iloc[0]['Asset_A']
        ticker_B = pairs_df.iloc[0]['Asset_B']
        
        master_df = pd.DataFrame({
            'Asset_A': price_df[ticker_A],
            'Asset_B': price_df[ticker_B]
        }).dropna()
        
    except FileNotFoundError:
        raise FileNotFoundError("Data files missing in data/directory. Run cointegration_screener.py first")


    beta = calculate_hedge_ratio(master_df['Asset_A'], master_df['Asset_B'])

    master_df['spread'] = calculate_spread(master_df['Asset_A'], master_df['Asset_B'], beta)
    
    master_df['z_score'] = calculate_rolling_zscore(master_df['spread'])
    
    master_df['signal'] = generate_signals(master_df['z_score'])
    
    chart_filename = f"backtest_{ticker_A}_{ticker_B}.png"
    plot_signals(master_df, save_path=chart_filename)
    
   