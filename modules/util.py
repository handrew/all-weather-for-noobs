import pandas as pd
import quandl
import datetime
import numpy as np
import keyring

QUANDL_AUTH_TOKEN = keyring.get_password('handrew', 'quandl')
PRICE_FIELD = 'Adj_Close'
DEFAULT_VOL_WINDOW = 200 # a little less than a year 


def get_returns(ticker, start=datetime.datetime(1940, 1, 1), end=datetime.datetime.now(), period=1):
	df = quandl.get('EOD/' + ticker, authtoken=QUANDL_AUTH_TOKEN)
	df['Returns'] = df[PRICE_FIELD].pct_change(period)
	df['Log Returns'] = np.log(df[PRICE_FIELD]) - np.log(df[PRICE_FIELD].shift(1))
	return df


# we want variance so that when we sum, we can just do the straight sum
def get_annualized_variance_of_series(series, window=DEFAULT_VOL_WINDOW):
	window_std = np.std(series.tail(window))
	variance = window_std ** 2
	ann_var = variance * np.sqrt(252) # 252 is number of trading days in a year
	return ann_var