#changelog
all noteable changes to this project will be documented in this file 

## 2026-07-14
### changed
- combined `run_cointegration_screen()` and `find_tradable_pairs()` into a single function 
- sourced cointegration p-value threshold dynamically from `config.yaml` throught the script instead of hardcoded limit
- optimised loop using index-based tracking (`idx_A` and `idx_B`) to prevent comparing an asset to itself or running duplicate tests
- cut the total number of cointegration calculations in half, making the script run faster

## 2026-07-13
### added
- created `cointegration-screener.py` core pipeline.
- implemented full matrix engle-granger cointegration screening across all configured asset pairs
- added dynamic YAML configuration loading for tickers and date ranges
- added p-value filtering functionality with thresholds sourced from `config.yaml`
- handled empty result edge cases and direct tabular data printing
