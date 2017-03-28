from modules.implied_vol import *

WEIGHTS_FILE = "output/weights.csv"

###############################################
# INPUT HERE

TICKERS = {
	"stocks": ['VTI', 'VEA'], 
	"commodities": ['DBC'], 
	"corporate credit": [],
	"EM credit": [],  # empty for now, can add
	"nominal bonds": ['TLT', 'HYD'], 
	"inflation-linked": ['GLD']
}

TICKER_VOLATILITY_OVERRIDES = {}
# TICKER_VOLATILITY_OVERRIDES = get_implied_volatilities_for_tickers(['TLT', 'GLD', 'TLT', 'VEA', 'DBC', 'HYG', 'VTI', 'VGK'])

VOL_WINDOW = 60

###############################################

print ">> Outputting to %s" % WEIGHTS_FILE