"""EqualWeightPortfolio object definition.
"""

from .portfolio import Portfolio


class EqualWeightPortfolio(Portfolio):
    """Creates uniform weights across given assets."""

    def __init__(self, assets, volatility_target=None):
        super(EqualWeightPortfolio, self).__init__(
            assets, volatility_target=volatility_target
        )

    def optimize(self, as_of_date=None):
        """
        @param as_of_date: datetime object
        @return: {asset_name: {"asset": Asset, "weight": float}}
        """
        weights = [1.0 / len(self.assets)] * len(self.assets)

        collapsed_weights = self.collapse_weights(self.assets, weights, as_of_date)

        if self.volatility_target:
            collapsed_weights = self.scale_weights_to_vol_target(
                collapsed_weights, as_of_date
            )

        return collapsed_weights
