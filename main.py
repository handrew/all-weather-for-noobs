import click
import datetime

import util
from util.stock import Stock
from util.backtester import SanityBacktester
from util import RiskParityPortfolio, EqualWeightPortfolio


@click.command()
@click.option("--vol", default=0.15, help="Volatility target (std dev).")
@click.option("--start", default="2007-10-19", help="Start date.")
@click.option("--end", default=datetime.datetime.now(), help="End date.")
@click.option("--out", default="backtest.csv", help="End date.")
@click.option("--benchmark", default="VTI", help="End date.")
def all_weather(vol, start, end, out, benchmark):
    """Calculate risk parity portfolio per All Weather."""
    print("\nGetting stocks...")
    bm = Stock(benchmark, "Benchmark")
    vti = Stock("VTI", "Stocks (VTI)")
    dbc = Stock("DBC", "Commodities (DBC)")
    gld = Stock("GLD", "Gold (GLD)")
    tlt = Stock("TLT", "Long-term Bonds (TLT)")

    print("\nForming portfolios...")
    vol_target = vol
    rg = RiskParityPortfolio([vti, dbc], volatility_target=vol_target)
    ri = RiskParityPortfolio([gld, dbc], volatility_target=vol_target)
    fg = RiskParityPortfolio([tlt, gld], volatility_target=vol_target)
    fi = RiskParityPortfolio([tlt, vti], volatility_target=vol_target)
    all_weather = EqualWeightPortfolio([rg, ri, fg, fi])

    print("\nBacktesting...")
    start = datetime.datetime.strptime(start, "%Y-%m-%d")
    if isinstance(end, str):
        end = datetime.datetime.strptime(end, "%Y-%m-%d")

    all_weather_bt = SanityBacktester(all_weather)
    benchmark = SanityBacktester(EqualWeightPortfolio([bm]))

    aw_pcts = all_weather_bt.backtest(start_date=start, end_date=end)
    benchmark_pcts = benchmark.backtest(start_date=start, end_date=end)

    print(
        "All Weather Sharpe: %0.3f" % util.print_annualized_sharpe(aw_pcts.sum(axis=1))
    )

    all_weather_indexed = util.one_index(aw_pcts.sum(axis=1).dropna())
    benchmark_indexed = util.one_index(benchmark_pcts[benchmark_pcts.columns[0]].dropna())

    all_weather_indexed["All Weather"] = all_weather_indexed["Value"]
    benchmark_indexed["Benchmark"] = benchmark_indexed["Value"]
    del all_weather_indexed["Value"]
    del benchmark_indexed["Value"]

    total = all_weather_indexed.join(benchmark_indexed)
    total.dropna().to_csv(out)

    print("Weights for today:")
    weights = all_weather.optimize()
    for key in weights.keys():
        print(key, "\t\t", weights[key]["weight"])


if __name__ == "__main__":
    all_weather()
