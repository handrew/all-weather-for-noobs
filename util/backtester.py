import pdb
import logging
import datetime
import numpy as np
import pandas as pd
from . import util
from .portfolio import Portfolio

SLIPPAGE = 0.005
TRADING_COST = 0.0005


class SanityBacktester(object):
    """SanityBacktester takes a Portfolio and simply calculates the theoretical
    weights at every particular day (within a rebalance period) and weights the
    daily returns of each asset.

    Can be used for a simple Sharpe ratio calculation.
    """

    def __init__(self, portfolio, trading_cost=TRADING_COST, slippage=SLIPPAGE):
        """
        Constructor for SanityBacktester

        @param portfolio: Portfolio object
        @param capital: beginning capital
        @param trading_cost: percentage of trade value
        @param slippage: percentage of trading cost, always
        going to be adversarial
        """
        self.portfolio: Portfolio = portfolio
        self.trading_cost: float = trading_cost
        self.slippage: float = slippage
        self.leverage_ratios = []
        self.exposures = []

        self.symbol_to_asset = {
            p.symbol: p for p in portfolio.tradeable_assets if isinstance
        }

    def _get_asset_from_symbol(self, name):
        return self.symbol_to_asset[name]

    def plot_leverage_ratios(self):
        df = pd.DataFrame(
            self.leverage_ratios, columns=["Date", "Leverage Ratio"]
        ).set_index("Date")

        df.plot()
        return df

    def plot_exposures(self):
        df = pd.DataFrame(self.exposures, columns=["Date", "Net Exposure"]).set_index(
            "Date"
        )

        df.plot()
        return df

    def backtest(
        self,
        start_date: datetime.datetime,
        end_date: datetime.datetime,
        rebalance_period=60,
        assets_to_include=[],
        weight_threshold=None,
        debug_csv="",
    ) -> pd.DataFrame:
        """
        Returns a pandas DataFrame with the return of the portfolios and
        weights.

        @param start_date: datetime object
        @param end_date: datetime object
        @param rebalance_period: int denoting periodicity of rebalancing
        @param weight_threshold: float denoting the lowest absolute value
        acceptable for weights to consider
        @param assets_to_include: list of the names of assets to include
        @return: pandas DataFrame
        """

        ########################
        # Get pct change dict
        ########################
        pcts: pd.DataFrame = self.portfolio.asset_df.pct_change()
        pcts = pcts[(pcts.index >= start_date) & (pcts.index <= end_date)]

        ########################
        # Get simulated weights
        ########################
        all_dates = pcts.index[rebalance_period + 1 :]
        rebalance_date: datetime.datetime = all_dates[0]

        all_weights = []
        last_weights = None

        for date in all_dates:
            if date >= rebalance_date:
                try:
                    logging.info("Rebalancing for date: %s" % str(date))
                    weights = self.portfolio.optimize(date)

                    # get total exposure
                    exposures = [weights[name]["weight"] for name in weights]
                    total_exposure = np.sum(exposures)
                    self.exposures.append((date, total_exposure))
                    logging.info("Net exposure: %0.3f" % total_exposure)

                    # get leverage ratio
                    leverage_ratio = np.sum([abs(exposure) for exposure in exposures])
                    logging.info("Leverage ratio: %0.3f" % leverage_ratio)
                    self.leverage_ratios.append((date, leverage_ratio))
                except IndexError as e:
                    msg = "Backtester.py: " + str(e)
                    logging.debug(msg)
                    rebalance_date = date
                    continue

                last_weights = weights
                rebalance_date = rebalance_date + datetime.timedelta(rebalance_period)

            curr_weights = {
                last_weights[name]["asset"].symbol: last_weights[name]["weight"]
                for name in last_weights
            }
            curr_weights["date"] = date
            all_weights.append(curr_weights)

        weights_df = pd.DataFrame(all_weights)
        weights_df = weights_df.set_index("date")

        ########################
        # Cull assets
        ########################
        if weight_threshold:
            weights_df[weights_df.abs() < weight_threshold] = 0.0
            # TODO may want to think about distributing the spare
            # allocation to remaining assets

        if assets_to_include:
            weights_columns = weights_df.columns
            for symbol in weights_columns:
                asset = self._get_asset_from_symbol(symbol)
                if asset.name in assets_to_include:
                    continue
                else:
                    weights_df[symbol] = 0.0

        if debug_csv:
            debug_df = pcts.copy()
            debug_df = debug_df.join(weights_df, rsuffix="_weights")
            debug_df.to_csv(debug_csv)

        ########################
        # Get simulated weighted returns
        ########################
        weighted_pcts = pcts.copy().shift(-1)
        weighted_pcts = weighted_pcts[weighted_pcts.index >= weights_df.index[0]]

        weights_cols = set(weights_df.columns)
        pcts_cols = set(weighted_pcts.columns)
        cols_in_both = weights_cols.intersection(pcts_cols)
        for col in cols_in_both:
            weighted_pcts[col] = weighted_pcts[col] * weights_df[col]  # \
            # * leverage_ratio
        return weighted_pcts
