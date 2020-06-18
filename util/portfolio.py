"""Base file for Portfolio interface."""

import collections
import numpy as np
import pandas as pd

from .asset import Asset
from . import util


class Portfolio(object):
    """Class for standard interface for portfolio construction."""

    def __init__(self, assets, window=60, periodicity=1, volatility_target=0.1):
        """Accepts a list of Asset or Portfolio

        @param assets: list of Asset or Portfolio
        @param window: int, volatility window
        @param periodicity: int, return interval, 1 for daily
        @param volatility_target: float from 0 to 1, to denote target vol
        """

        # Must be all Portfolio objects or all Asset objects.
        num_portfolio_objs = sum([isinstance(a, Portfolio) for a in assets])
        assert (num_portfolio_objs == len(assets)) or (num_portfolio_objs == 0)

        self.is_portfolio_of_portfolios = num_portfolio_objs == len(assets)

        # Must all be unique.
        asset_names = [asset.name for asset in assets if isinstance(asset, Asset)]
        assert len(asset_names) == len(set(asset_names))  # no duplicates
        assert "cash" not in [name.lower() for name in asset_names]

        self.assets = assets
        self.window = window
        self.periodicity = periodicity
        if volatility_target:
            self.volatility_target = volatility_target ** 2
        else:
            self.volatility_target = None

        # self.tradeable_assets is different from self.assets in that assets
        # may also include Portfolios.
        self.tradeable_assets = self._get_all_asset_objs(assets)

        first_symbol = self.tradeable_assets[0].symbol
        self.asset_df = self.tradeable_assets[0].price.to_frame(first_symbol)
        for i in range(1, len(self.tradeable_assets)):
            curr_asset = self.tradeable_assets[i]
            self.asset_df = self.asset_df.join(
                curr_asset.price.to_frame(curr_asset.symbol)
            )

    def _get_all_asset_objs(self, asset_list) -> list:
        """Helper function for init, to get all tradeable assets
        possibly nested within Portfolio objects
        """
        _assets = []
        for asset in asset_list:
            if hasattr(asset, "assets"):  # isinstance(a, Port.) didn't work
                sub_assets = self._get_all_asset_objs(asset.assets)
                for sa in sub_assets:
                    if sa not in _assets:
                        _assets.append(sa)
            elif asset not in _assets:
                _assets.append(asset)

        return _assets

    def _no_empty_indicators(self, indicators) -> bool:
        nan_dropped_series = []
        for indicator in indicators:
            if isinstance(indicator, Indicator) or (isinstance(indicator, Signal)):
                indicator = indicator.value
            nan_dropped_series.append(indicator.dropna())

        lengths = [len(item) for item in nan_dropped_series]
        empty_entries = [length == 0 for length in lengths]
        return not any(empty_entries)

    def optimize(self, as_of_date=None) -> dict:
        """Meant to be overriden in child classes."""
        pass

    def get_all_indicators(self) -> list:
        """Get all indicators used within a Portfolio."""
        indicators = getattr(self, "indicators", [])
        for asset in self.assets:
            if isinstance(asset, Portfolio):
                indicators.extend(getattr(asset, "indicators", []))
        return indicators

    def print_all_indicators(self):
        """Print all indicators, using get_all_indicators."""
        indicators = self.get_all_indicators()
        indicators = sorted(indicators, key=lambda ind: ind.index[0])
        for indicator in indicators:
            dates = str(indicator.index[0]) + "\t" + str(indicator.index[-1])
            print(dates + "\t" + indicator.name)

    def print_all_tradeable_assets(self):
        """Print all tradeable assets."""
        _assets = sorted(self.tradeable_assets, key=lambda asset: asset.price.index[0])
        for asset in _assets:
            price = asset.price
            print(str(price.index[0]) + "\t" + asset.name)

    def collapse_weights(self, assets_or_portfolios, weights, as_of_date=None):
        """Given a list of assets or portfolios and a corresponding list of
        weights, create an allocation of weights to individual Assets,
        per the multiplication of the weights vector against any
        Portfolio's weights.

        @param assets_or_portfolios: list of Asset or Portfolio
        @param weights: list of weights
        @return: {asset_name: {"asset": Asset, "weight": float}}
        """

        # Set up search for recombination.
        asset_dict = {
            item.symbol: item
            for item in assets_or_portfolios
            if isinstance(item, Asset)
        }

        # Set up combined weights.
        combined_weights = collections.defaultdict(lambda: 0)
        for i, item in enumerate(assets_or_portfolios):
            if isinstance(item, Asset):
                combined_weights[item.symbol] += weights[i]
            else:
                portfolio_weights = item.optimize(as_of_date=as_of_date)
                for name in portfolio_weights:
                    asset = portfolio_weights[name]["asset"]
                    weight = portfolio_weights[name]["weight"]
                    # add it to the recall dict if not already
                    if asset.symbol not in asset_dict:
                        asset_dict[asset.symbol] = asset
                    combined_weights[asset.symbol] += weights[i] * weight

        # Reshape in final form.
        collapsed_weights = {}
        for symbol in combined_weights:
            curr_asset = asset_dict[symbol]
            collapsed_weights[curr_asset.name] = {
                "asset": curr_asset,
                "weight": combined_weights[symbol],
            }
        return collapsed_weights

    def create_synthetic_returns(self, portfolio, as_of_date):
        """Create synthetic returns of a portfolio as of a certain date
        """
        daily_pcts = self.asset_df.pct_change()
        daily_pcts = daily_pcts[daily_pcts.index <= as_of_date]

        weights = portfolio.optimize(as_of_date=as_of_date)

        weighted_returns = []
        for asset_name in weights:
            asset = weights[asset_name]["asset"]
            weight = weights[asset_name]["weight"]
            weighted_returns.append(weight * daily_pcts[asset.symbol])

        returns = weighted_returns[0]
        for i in range(1, len(weighted_returns)):
            curr_returns = weighted_returns[i].reindex(returns.index, method="nearest")
            returns = returns + curr_returns

        indexed = util.one_index(returns.dropna())
        return indexed

    def covariance_matrix(
        self,
        assets_to_use=None,
        use_portfolios_only=False,
        window=60,
        periodicity=1,
        min_periods=None,
        as_of_date=None,
        annualize=True,
    ):
        """Return pandas dataframe

        @assetsToUse: None if include everything, otherwise list of Asset.
        Used by LongShortPortfolio to the vol of a subset of Assets.

        @window: int, lookback

        @periodicity: int, usually 1 for 1 day at a time

        @min_periods: int, usually None. if not None then it will NaN out
        entries that don't have enough backhistory

        @use_portfolios_only: bool, False if want to use Assets from
        self.asset_df, True if want to use Portfolio from self.assets AND
        self.is_portfolio_of_portfolios

        @as_of_date: datetime object

        @annualize: bool
        """
        if use_portfolios_only:
            assert self.is_portfolio_of_portfolios
            assert assets_to_use is None

        # Set default as_of_date.
        if not as_of_date:
            as_of_date = self.asset_df.index[-1]

        # If we care about the covariance of entire portfolios, create
        # synthetic return series.
        if use_portfolios_only and self.is_portfolio_of_portfolios:
            # create synthetic return series
            subportfolio_returns = []
            for portfolio in self.assets:
                indexed = self.create_synthetic_returns(portfolio, as_of_date)
                subportfolio_returns.append(indexed)

            # join the synthetic returns
            all_indexed = subportfolio_returns[0]
            for i in range(1, len(subportfolio_returns)):
                all_indexed = all_indexed.join(
                    subportfolio_returns[i], rsuffix="_%d" % i
                )

            pct_returns = all_indexed.pct_change(periodicity).iloc[::periodicity]
        else:
            as_of_df = self.asset_df[self.asset_df.index <= as_of_date]

            # Only keep certain assets.
            if assets_to_use is not None:
                keep_assets = [asset.symbol for asset in assets_to_use]
                as_of_df = as_of_df[keep_assets]

            # Get the right periodicity.
            pct_returns = as_of_df.pct_change(periodicity).iloc[::periodicity]

        # Finally, do the covariance calculation and annualize if necessary.
        if min_periods:
            covariances = pct_returns.tail(window).cov(min_periods=min_periods)
        else:
            covariances = pct_returns.tail(window).cov()

        if annualize:
            covariances = covariances * (252.0 / periodicity)

        return covariances

    def get_portfolio_volatility(self, assets, weights, as_of_date):
        """Return variance (not standard deviation) of weighted portfolio
        returns.

        Calculated as w * covariance * w.T
        """
        if isinstance(weights, pd.Series):
            w = np.array([weights.values])
        else:
            w = np.array([weights])

        if assets is not None:
            assert len(assets) == len(weights)

        cov_mat = self.covariance_matrix(
            assets_to_use=assets,
            window=self.window,
            periodicity=self.periodicity,
            as_of_date=as_of_date,
        )

        left = w @ cov_mat
        portfolio_vol = (left @ w.T)[0][0]
        assert not np.isnan(portfolio_vol)
        return portfolio_vol

    def scale_weights_to_vol_target(self, collapsed_weights, as_of_date):
        """Scale weights to volatility target. Multiplies the portfolio by the
        right scale factor in *variance* terms, not stddev terms.
        """
        assets = [collapsed_weights[name]["asset"] for name in collapsed_weights]
        weights = [collapsed_weights[name]["weight"] for name in collapsed_weights]

        portfolio_vol = self.get_portfolio_volatility(assets, weights, as_of_date)

        vol_scale = np.sqrt(self.volatility_target / portfolio_vol)

        for name in collapsed_weights:
            collapsed_weights[name]["weight"] = (
                vol_scale * collapsed_weights[name]["weight"]
            )

        # Do a sanity check.
        scaled_weights = [
            collapsed_weights[name]["weight"] for name in collapsed_weights
        ]

        _portfolio_vol = self.get_portfolio_volatility(
            assets, scaled_weights, as_of_date
        )

        assert self.volatility_target - _portfolio_vol <= 1e-4
        return collapsed_weights
