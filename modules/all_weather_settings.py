from modules.implied_vol import *

WEIGHTS_FILE = "output/weights.csv"

###############################################
# INPUT HERE

TICKERS = {
	"stocks": ['VTI', 'VEA', 'VWO'], 
	"commodities": ['DBC'],
	"corporate credit": [],
	"EM credit": [],  # empty for now, can add
	"nominal bonds": ['TLT'], 
	"inflation-linked": ['GLD']
}

TICKER_VOLATILITY_OVERRIDES = {}
OVERRIDE_TICKERS = [
	'TLT', 'GLD', 'VWO', 'DBC', 'HYG', 'VTI', 'VGK', 'EWJ'
]
# TICKER_VOLATILITY_OVERRIDES = get_implied_volatilities_for_tickers(OVERRIDE_TICKERS)

VOL_WINDOW = 60

###############################################

print ">> Outputting to %s" % WEIGHTS_FILE