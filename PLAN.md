#Pairs Trading Backtester

This project will be an automated system designed to find pairs of stocks that historically move together. 
When the historical relationship between these two stocks temporarily break (one becomes overpriced while the other becomes underpriced) the system flags a potential trade. 
Then, the system simulates short selling the expensive stock and buying the cheaper one, betting that their prices will eventually snap back to their historical average.

And to prove that this strategy actually works before risking any real money, the system includes a backtester. This engine will look backwards at the last few years of historical market data, pretend to execute trades automatically based on the preestablished strategy rules, factoring in transaction fees and tracks our cash balance over time so we can see what our final returns and risks would have been.


## Plan

### 1. Setup & Config
- Create a `config.yaml` file to hold stock list, date ranges and statistical cut offs, and portfolio settings in one place. 
- Writes a path loader function using `os.path` so the configuration loads automatically whether the code is run from the terminal or from inside the notebook folder. 

### 2. Data Ingestion & Cointegration Screener 
#### Function no.1 - `load_config()`
- Reads `config.yaml` file using path independent logic
- __Returns__ target stock list, date parameters and p-value thresholds as a python dictionary
#### Function no.2 - `download_market_data`
- Takes ticker list and date ranges and uses `yfinance` to download historical closing prices 
- cleans up missing entries using `.dropna()`
- __Returns__ a Pandas DataFrame
#### Function no.3 - `run_cointegration_screen()`
- Takes price DataFrame and runs Engle-Granger cointegration test (`coint` from `statsmodels`)
- Stores resulting p-values in a symmetrical matrix
- __returns__ a symmetrical Pandas DataFrame matrix containing p-valuesfor all pairs
#### Function no.4 - `find_tradable_pairs()` 
- Scans completed p-value matrix and filters out asset combinations where p-value is less than 0.05
- __Returns__ finalised list of statistically valid pairs
#### Main execution
- Serves as scripts entry point when run directly from the terminal
- coordinates the workflow by calling functions in order
- filters and displays final results in a clean, readable terminal printout

### 3. Spread Modeling & Trading Signals
Takes verified stock pairs from 2. and calculates their historical price gap (spread) using linear regression and then generates entry/exit trading signals based on statistical deviations and visualises the results

#### Function no.1 - `calculate_hedge_ratio()`
- Takes prices of Asset A and Asset B
- Runs an ordinary least squares (OLS) regression using `statsmodels` to find hedge ratio (hedge ratio represents relationship slope between two assets)
- __Returns__ hedge ratio float value

$$Y = \beta X + \alpha$$

#### Function no.2 - `calculate_spread()`
- Takes the prices of Asset A, Asset B and the calculated hedge ratio
- Subtracts the scaled price of Asset B from Asset A (spread = stock A - (Hedge ratio * Stock B))
- __Returns__ Pandas Series representing historical spread over time

$$Spread_t = \text{Price}_{A,t} - (\beta \times \text{Price}_{B,t})$$

#### Function no.3 - `calculate_zscore()`
- Takes raw spread series and a rolling lookback window parameter
- Calculates the rolling mean and rolling Standard deviation of the spread to turn the raw gap into a standardized Z-score
- __Returns__ pandas series of rolling Z-scores

#### Function no.4 - `generate_signals()`
- Takes Z-score Series, an entry threshold and an exit threshold
- Flags when to long the spread (-1), short the spread (+1) or exit the position completely (0)
- __Returns__ a pandas dataframe containing historical stock prices, rolling z-score and signal flags

#### Function no.5 - `plot_signals()`
- Takes the DataFrame from signal generator 
- Uses `matplotlib` to generate a two panel chart where the top panel displays the raw stock prices and spread, while the bottom panel shows the rolling Z-score alongside horizontal lines for entry and exit thresholds

#### Main Execution Block
- Pulls a top performing cointegration pair from section 2
- executes the signal generator pipeline
- calls plot_signals() to render and save threshold chart


### 4. Backtesting Engine and Performance Reports
This script uses a dedicated python class to simulate historical python execution of determined trading signals, tracks portfolio over time and calculates institutional risk adjusted performance matrices

#### Class structure - `class backtester`
- `__init__(self, config_dict)`
- initializes the backtest environment by unpacking parameters directly from configuration settings
- assigns starting cash balance and transaction fee parameters dynamically

#### Class method no.1 - `simulate_positions()`
- Takes the historical price DataFrame and raw signal flags from Section 3
- Loops through time to determine when the portfolio is actively (1) long the spread (buying Asset A, shorting Asset B), (2) short the spread (shorting Asset A, buying Asset B) or (3) sitting in cash
- __Returns__  modified DataFrame containing historical portfolio position states

$$P_t = (\text{Price}_{A,t} - \text{Price}_{A,\text{entry}}) - \beta \times (\text{Price}_{B,t} - \text{Price}_{B,\text{entry}})$$


#### Class Method no.2 - `apply_transaction_costs()`
- Tracks when our position states change 
- Deducts realistic execution fees and slippage parameters from cash balance using the `transaction_cost` value set during initialisation
- __Returns__ - (directly updates internal cash and asset values)

$$\text{Fee} = (\text{Value}_A + \text{Value}_B) \times \text{transaction\_cost}$$

#### Class Method no.3 - `calculate_equity_curve()`
- Combines cash balances, open position values and price changes day by day
- Generates continuous daily total portfolio value series
- __Returns__  Pandas Series representing our historical equity curve

$$\text{Equity}_t = \text{Cash}_t + P_t$$

#### Class Method no.4 - `generate_performance_metrics()`
- Takes finalized daily equity curve Series 
- Calculates core metrics: total return, annualized Volatility, maximum drawdown (peak-to-trough downside risk) and the Sharpe Ratio (risk-adjusted return).
- __Returns__ a dictionary of performance statistics and prints a clean report to the terminal

$$\text{Total Return} = \frac{\text{Equity}_{\text{final}} - \text{Equity}_{\text{initial}}}{\text{Equity}_{\text{initial}}}$$

$$r_t = \frac{\text{Equity}_t - \text{Equity}_{t-1}}{\text{Equity}_{t-1}}$$

$$\sigma_{\text{ann}} = \text{std}(r_t) \times \sqrt{252}$$

$$\text{Sharpe Ratio} = \frac{\text{mean}(r_t) \times 252}{\sigma_{\text{ann}}}$$

$$\text{Max Drawdown} = \max \left( \frac{\text{Peak}_t - \text{Equity}_t}{\text{Peak}_t} \right)$$

#### Main Execution Block - `if __name__ == "__main__"`
- Imports generated signal data from Section 3 and the configuration dictionary from Section 1
- Instantiates the `Backtester` class using the configuration parameters
- Runs the backtest pipeline and outputs the final performance summary report to the console
