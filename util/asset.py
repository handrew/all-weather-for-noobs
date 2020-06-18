# -*- coding: utf-8 -*-
import abc
import numpy as np
import pandas as pd
from .timeseries import TimeSeries


class Asset(TimeSeries):
    __metaclass__ = abc.ABCMeta

    def __init__(self, symbol, name, asset_type, source, interval='monthly'):
        super(Asset, self).__init__(source)
        self.name = name
        self.symbol = symbol
        self.asset_type = asset_type
        try:
            self.get(symbol, interval=interval)
        except TypeError as e:
            raise(
                TypeError("base.py, Asset: " + str(e) + " Symbol: %s" % symbol)
            )

    def __eq__(self, other):
        symbols_same = (self.symbol == other.symbol)
        types_same = (self.asset_type == other.asset_type)
        return symbols_same and types_same

    @property
    def price(self) -> pd.DataFrame:
        price_field: Union[str, list] = \
            self.engine.config[self.asset_type]['price']

        if isinstance(price_field, list):
            for field in price_field:
                if field in self.data.columns:
                    df = self.get_attribute(field)
                    df = df.replace(0, np.nan).ffill()
                    return df

            raise TypeError("""
                Could not find price field for {}. Columns were: {}
            """.format(self.name, str(self.data.columns)))

        df = self.get_attribute(price_field)
        df = df.replace(0, np.nan).ffill()
        return df

    def volatility(self,
                   window=30,
                   periodicity=1,
                   as_of_date=None,
                   annualize=True) -> pd.Series:
        """Returns variance, not standard deviation.
        """
        if not as_of_date:
            as_of_date: datetime.datetime = self.price.index[-1]

        price: pd.Series = self.price[self.price.index <= as_of_date]

        # ::per means to take every per-th row
        pcts: pd.Series = price.pct_change(periodicity).iloc[::periodicity]
        vol: pd.Series = pcts.rolling(window=window).std() ** 2
        if annualize:
            vol = vol * (252.0 / periodicity)

        return vol

    def last_volatility(self,
                        window=30,
                        periodicity=1,
                        as_of_date=None,
                        annualize=True,
                        average_with_expanding_mean=True) -> float:
        vol_series: pd.Series = self.volatility(
            window=window,
            periodicity=periodicity,
            as_of_date=as_of_date,
            annualize=annualize
        )

        if len(vol_series):
            last_vol = vol_series.iloc[-1]

            if average_with_expanding_mean:
                exp_mean = vol_series.expanding(min_periods=1).mean()

                last_mean_vol = exp_mean.iloc[-1]
                last_vol = np.mean([
                    # take sqrt to be in stddev terms
                    np.sqrt(last_vol), np.sqrt(last_mean_vol)
                ]) ** 2   # take to the second power to put back in var terms

            return last_vol

        return None

    def momentum(self, window=30, as_of_date=None) -> pd.Series:
        if not as_of_date:
            as_of_date = self.price.index[-1]

        pcts = self.price[self.price.index <= as_of_date].pct_change(window)

        return pcts
