# The Poor Man's All Weather sStrategy

## Disclaimer

This code is developed for academic and illustrative purposes only and shall not be construed as financial, tax or legal advice or recommendations. The accuracy of the data on this site cannot be guaranteed. Users should use the information provided at their own risk and should always do their own due diligence before any investment decision. The information on this site does not constitute a solicitation for the purchase or sale of securities. No representation or implication is being made that using the information provided here will generate profits or ensure freedom from losses. All ideas and material presented are entirely those of the author and do not necessarily reflect those of the publisher. 

CFTC RULE 4.41 – HYPOTHETICAL OR SIMULATED PERFORMANCE RESULTS HAVE CERTAIN LIMITATIONS. UNLIKE AN ACTUAL PERFORMANCE RECORD, SIMULATED RESULTS DO NOT REPRESENT ACTUAL TRADING. ALSO, SINCE THE TRADES HAVE NOT BEEN EXECUTED, THE RESULTS MAY HAVE UNDER-OR-OVER COMPENSATED FOR THE IMPACT, IF ANY, OF CERTAIN MARKET FACTORS, SUCH AS LACK OF LIQUIDITY. SIMULATED TRADING PROGRAMS IN GENERAL ARE ALSO SUBJECT TO THE FACT THAT THEY ARE DESIGNED WITH THE BENEFIT OF HINDSIGHT. NO REPRESENTATION IS BEING MADE THAT ANY ACCOUNT WILL OR IS LIKELY TO ACHIEVE PROFIT OR LOSSES SIMILAR TO THOSE SHOWN.

## Why All Weather?

All Weather is a risk parity strategy developed and used by Bridgewater. Much has been written – by <a target="_blank" href="https://www.bridgewater.com/research-library/risk-parity/">Bridgewater</a> and <a href="https://www.aqr.com/Insights/Research/White-Papers/Understanding-Risk-Parity" target="_blank">others</a> – about the advantages of risk parity over modern portfolio theory.

## Modifications

The most salient modifications I made to the strategy are:

* Variances are assumed to be independent (i.e., they are summed without adjusting for covariances)
* Gold was used as a substitute for inflation-protected securities (and long-term bonds for bonds) because retail investors do not have easy access to leverage, so more volatile substitutes had to be selected
* ETFs used: Growth rising (VTI, DBC), growth falling (TLT, GLD), inflation rising (GLD, DBC), inflation falling (TLT, VTI)