import os
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import yaml

base_dir = os.path.dirname(os.path.dirname(__file__))
config_path = os.path.join(base_dir, "config.yaml")

def load_config(path = config_path):
    with open(path, "r") as file:
        return yaml.safe_load(file)
    
class backtester:
    def __init__(self, config):
        self.config = config
        self.initial_capital = config["portfolio"]["initial_capital"]
        self.trransaction_cost = config["portfolio"]["transaction_cost"]
        self.borrow_fee = config["portfolio"]["short_borrow_fee"] / 252.0

    def apply_transaction_costs(self, position_series):
        trades = position_series.diff().abs().fillna(0)
        return trades * self.trransaction_cost
    
    def calculate_equity_curve(self, df):
        df = df.copy()

        df["position"] = df["signal"].shift(1).fillna(0)
        df["ret_a"] = df["price_a"].pct_change().fillna(0)
        df["ret_b"] = df["price_b"].pct_change().fillna(0)
        df["spread_ret"] = df["ret_a"] - (df["beta"].shift(1) * df["ret_B"])

        cost_pct = self.apply_transaction_costs(df["position"])

        conditions =[
            df["position"] == 1,
            df["position"] == -1,
            df["position"] == 0 
        ]

        choices = [
            df["spread_ret"] - cost_pct,
            -df["spread_ret"] - cost_pct - self.borrow_fee,
            0.0
        ]


        df["strategy_return"] = np.select(conditions, choices, default - 0.0)