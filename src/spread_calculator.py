import os
import yaml
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

base_dir = os.path.dirname(os.path.dirname(__file__))
config_path = os.path.join(base_dir, "config.yaml")

def load_config(path = config_path):
    with open(path, 'r') as file:
        return yaml.safe_load(file)
    
def calculate_hedge_ratio(series_a, series_b, window):
    rolling_cov = series_a.rolling(window=window).cov(series_b)
    rolling_var = series_b.rolling(window=window).var()
    beta = rolling_cov / rolling_var
    return beta

def calculate_spread(series_a, series_b, hedge_ratio):
    spread = series_a - (hedge_ratio * series_b)
    return spread

def calculate_rolling_zscore(spread, window):
    mean = spread.rolling(window=window).mean()
    std = spread.rolling(window=window).std()
    z_scores = (spread - mean) / std
    return z_scores

def generate_signals(z_scores, config):
    """
    generates trading signals based on z score entry and exit thresholds

    Returns:
        pd.Series: signal flags matching the input index:
             1 = long the spread 
             -1 = short the spread 
             0 = neutral (no position)
    """
    entry = config["zscore"]["entry_threshold"]
    exit = config["zscore"]["exit_threshold"]
    stop = config["zscore"]["stop_loss_threshold"]

    signals = np.zeros(len(z_scores))
    pos = 0

    for i, z in enumerate(z_scores):
        if np.isnan(z):
            continue
        if abs(z) >= stop:
            pos = 0
        elif pos == 0:
            if z > entry:
                pos = -1
            elif z < -entry:
                pos = 1
        elif pos == 1 and z >= -exit:
            pos = 0
        elif pos == -1 and z <= exit:
            pos = 0

        signals[i] = pos

    return pd.Series(signals, index = z_scores.index, name = "signal")

def calculate_spread_metrics (prices_df, ticker_a, ticker_b, config):
    """
    takes raw price data and outputs calculated beta, spread, z scores and trage signals
    """
    df = pd.DataFrame({
        "Asset_A": prices_df[ticker_a],
        "Asset_B": prices_df[ticker_b]
    })

    hedge_win = config["strategy"]["hedge_lookback"]
    z_win = config["zscore"]["lookback_window"]

    df["beta"] = calculate_hedge_ratio(df["Asset_A"], df["Asset_B"], hedge_win)
    df["spread"] = calculate_spread(df["Asset_A"], df["Asset_B"], df["beta"])
    df["z_score"] = calculate_rolling_zscore(df["spread"], z_win)
    df["signal"] = generate_signals(df["z_score"], config)

    return df.dropna()

def plot_signals (df, ticker_a, ticker_b, config, save_path = "plot.png"):
    entry = config["zscore"]["entry_threshold"]
    exit = config["zscore"]["exit_threshold"]
    stop = config["zscore"]["stop_loss_threshold"]

    fig, (ax1, ax2) = plt.subplots(2,1, figsize=(12,10), sharex = True)

    #PANEL 1 - portfolio spread
    ax1.plot(
        df.index,
        df["spread"],
        label=f"Spread ({ticker_a} vs {ticker_b})",
        color="blue",
        alpha=0.75,
        linewidth=1.2
    )
   
    ax1.set_title(f"Pairs spread & z-scores: {ticker_a} vs {ticker_b}", fontsize=14, fontweight="bold")
    ax1.set_ylabel("Spread Value", fontsize=12)
    ax1.legend(loc="upper left")
    ax1.grid(True, linestyle="--", alpha=0.4)

    #PANEL 2 - rolling z score and thresholds
    ax2.plot(df.index, df["z_score"], label="Z-Score", color="black", lw=1)

    ax2.axhline(entry, color="red", linestyle="--", label=f"Entry Threshold (±{entry})")
    ax2.axhline(-entry, color="red", linestyle="--")
    ax2.axhline(exit, color="green", linestyle="--", label=f"Exit Threshold (±{exit})")
    ax2.axhline(-exit, color="green", linestyle="--")
    ax2.axhline(stop, color="blue", linestyle="--", label=f"Stop Loss (±{stop})")
    ax2.axhline(-stop, color="blue", linestyle="--")

    ax2.set_ylim(-stop - 0.5, stop + 0.5)

    if exit != 0:
        ax2.axhline(-exit, color='green', linestyle=':', linewidth=1.2)
        
    ax2.fill_between(
        df.index,
        df["z_score"],
        0,
        where=(df["signal"] == 1),
        color="green",
        alpha=0.2,
        label="Long Spread(+1)"
    )

    ax2.fill_between(
        df.index,
        df["z_score"],
        0,
        where=(df["signal"] == -1), 
        color="red",
        alpha=0.15,
        label="Short Spread(-1)"
    )
      
    ax2.set_ylabel("Z-Score Standard Deviations", fontsize=12)
    ax2.set_xlabel("Date", fontsize=12)
    ax2.legend(loc="upper left")
    ax2.grid(True, linestyle="--", alpha=0.4)
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=300)
    print(f"chart rendered and saved to {save_path}")
    plt.show()

if __name__ == '__main__':
    config = load_config()
    
    data_dir = os.path.join(base_dir, "data")
    prices_path = os.path.join(data_dir, "historical_prices.csv")
    pairs_path = os.path.join(data_dir, "top_cointegrated_pairs.csv")

    prices = pd.read_csv(prices_path, index_col=0, parse_dates=True)
    pairs = pd.read_csv(pairs_path)

    ticker_a = pairs.iloc[0]["Asset_A"]
    ticker_b = pairs.iloc[0]["Asset_B"]

    spread_df = calculate_spread_metrics(prices, ticker_a, ticker_b, config)

    output_path = os.path.join(data_dir, "spread_signals.csv")
    spread_df.to_csv(output_path)
    print(f"Spread calculation complete for {ticker_a} / {ticker_b}. Saved to {output_path}")

    plot_path = os.path.join(data_dir, "spread_signals_plot.png")
    plot_signals(spread_df, ticker_a, ticker_b, config, save_path=plot_path)
        
       
    
   