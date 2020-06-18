"""RiskParityPortfolio object. Optimizes weights to be inversely proportional
to the volatility of each asset. This approach does not not assume any
correlations – for a risk parity approach that accounts for correlation, use
EqualRiskContributionPortfolio.
"""

import pdb
from typing import List
import numpy as np
import pandas as pd
from .asset import Asset
from .portfolio import Portfolio


class RiskParityPortfolio(Portfolio):
    """Optimizes weights to be inversely proportional to the volatility of each
    asset. This approach does not not assume any correlations – for a risk
    parity approach that accounts for correlation, use
    EqualRiskContributionPortfolio.
    """

    def __init__(self, assets, window=60, periodicity=1, volatility_target=0.1):
        has_portfolio_objs = any([isinstance(a, Portfolio) for a in assets])
        if has_portfolio_objs:
            raise ValueError(
                "RiskParityPortfolio can not " "accept Portfolio in param `assets`."
            )

        super(RiskParityPortfolio, self).__init__(
            assets,
            window=window,
            periodicity=periodicity,
            volatility_target=volatility_target,
        )

    def optimize(self, as_of_date=None):
        """Solves for inverse-volatility weights.

        @param as_of_date: datetime object
        @return: {asset_name: {"asset": Asset, "weight": float}}
        """

        most_recent_vols: List[float] = [
            asset.last_volatility(
                window=self.window, periodicity=self.periodicity, as_of_date=as_of_date
            )
            for asset in self.assets
        ]

        asset_df = pd.DataFrame([self.assets, most_recent_vols]).T
        asset_df.columns = ["asset", "vol"]
        asset_df = asset_df.dropna().reset_index()  # get rid of None vols

        weights_i: List[float] = []
        std_inv = 1.0 / np.sqrt(asset_df["vol"].astype(float))
        weights_i = list(std_inv / std_inv.sum())

        asset_df["weights"] = pd.Series(weights_i)

        # Make sure that volatility contributions are all the same.
        try:
            vol_contributions = (asset_df["weights"] ** 2) * asset_df["vol"]
            for i in range(1, len(vol_contributions)):
                diff = abs(vol_contributions[0] - vol_contributions[i])
                assert diff <= 1e-4
        except AssertionError:
            pdb.set_trace()

        # Put it in return format.
        allocations: dict = {}
        for i in range(len(asset_df)):
            curr_asset: Asset = asset_df["asset"].iloc[i]
            weight = asset_df["weights"].iloc[i]
            vol_cont = (weight ** 2) * asset_df["vol"].iloc[i]
            allocations[curr_asset.name] = {
                "asset": curr_asset,
                "weight": weight,
                "vol_contribution": vol_cont,
            }

        if self.volatility_target:
            # Scale to vol target.
            vol_contributions = [
                allocations[name]["vol_contribution"] for name in allocations
            ]
            portfolio_vol = np.sum(vol_contributions)
            vol_scale = np.sqrt(self.volatility_target / portfolio_vol)
            for name in allocations:
                allocations[name]["weight"] = allocations[name]["weight"] * vol_scale

            # Update vol contributions.
            asset_df["name"] = asset_df["asset"].apply(lambda x: x.name)
            for name in allocations:
                weight = allocations[name]["weight"]
                vol_cont = (weight ** 2) * asset_df[asset_df["name"] == name][
                    "vol"
                ].iloc[0]
                allocations[name]["vol_contribution"] = vol_cont

            # Check that everything is right.
            vol_contributions = [
                allocations[name]["vol_contribution"] for name in allocations
            ]
            try:
                diff = abs(np.sum(vol_contributions) - self.volatility_target)
                assert diff <= 1e-4

                for i in range(1, len(vol_contributions)):
                    diff = abs(vol_contributions[0] - vol_contributions[i])
                    assert diff <= 1e-4
            except AssertionError:
                pdb.set_trace()

        return allocations
