import datetime
import numpy as np
import yfinance as yf


PRICE_FIELD = "Adj Close"
DEFAULT_VOL_WINDOW = 200  # A little less than a year.


def get_returns(ticker,
                start=datetime.datetime(1940, 1, 1),
                end=datetime.datetime.now(),
                period=1):
    df = yf.download(ticker, period="max")
    df["Returns"] = df[PRICE_FIELD].pct_change(period)
    df["Log Returns"] = np.log(df[PRICE_FIELD]) \
        - np.log(df[PRICE_FIELD].shift(1))
    return df


# we want variance so that when we sum, we can just do the straight sum
def get_annualized_variance_of_series(series, window=DEFAULT_VOL_WINDOW):
    window_std = np.std(series.tail(window))
    variance = window_std ** 2
    ann_var = variance * 252  # 252 is number of trading days in a year
    return ann_var
