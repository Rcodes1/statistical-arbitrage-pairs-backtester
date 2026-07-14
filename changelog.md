#changelog
all noteable changes to this project will be documented in this file 

## 2026-07-14
### changed
- combined `run_cointegration_screen()` and `find_tradable_pairs()` into a single function 
- sourced cointegration p-value threshold dynamically from `config.yaml` throught the script instead of hardcoded limit


## 2026-07-14
### added
- created `cointegration-screener.py` core pipeline.
- implemented full matrix engle-granger cointegration screening across all configured asset pairs
- added dynamic YAML configuration loading for tickers and date ranges
- added p-value filtering functionality with thresholds sourced from `config.yaml`
- handled empty result edge cases and direct tabular data printing
