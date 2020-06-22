import click
import datetime

import util
from util.stock import Stock
from util.backtester import SanityBacktester
from util import RiskParityPortfolio, EqualWeightPortfolio

import yaml
import numpy as np


@click.command()
@click.argument("settings")
def all_weather(settings):
    """Calculate risk parity portfolio per All Weather."""
    settings = yaml.load(open(settings, "r"), Loader=yaml.Loader)

    # Set up dates.
    if "END_DATE" not in settings:
        settings["END_DATE"] = datetime.datetime.now()
    start = datetime.datetime.strptime(settings["START_DATE"], "%Y-%m-%d")
    end = settings["END_DATE"]
    if isinstance(end, str):
        end = datetime.datetime.strptime(end, "%Y-%m-%d")

    # Set up other variables.
    vol_target = settings["VOLATILITY_TARGET"]
    benchmark = settings["BENCHMARK_TICKER"]
    out = settings["OUTPUT_FILE"]

    print("Volatility target: {}%".format(vol_target * 100))
    print("Backtesting from %s to %s." % (start, end))
    print("Benchmarking against: %s" % benchmark)
    all_tickers = set(
        np.concatenate(list(settings["ENVIRONMENTS"].values()))
    ).union(set([benchmark]))

    print("\nGetting stocks...")
    cache = {
        ticker: Stock(ticker, ticker) for ticker in all_tickers
    }  # To avoid making unnecessary API calls.

    print("\nForming portfolios...")
    portfolios = {
        environment: RiskParityPortfolio(
            [
                cache[ticker]
                for ticker in settings["ENVIRONMENTS"][environment]
            ],
            volatility_target=vol_target,
        )
        for environment in settings["ENVIRONMENTS"]
    }
    all_weather = EqualWeightPortfolio(list(portfolios.values()))

    print("\nBacktesting...")

    all_weather_bt = SanityBacktester(all_weather)
    benchmark = SanityBacktester(EqualWeightPortfolio([cache[benchmark]]))

    aw_pcts = all_weather_bt.backtest(start_date=start, end_date=end)
    benchmark_pcts = benchmark.backtest(start_date=start, end_date=end)

    print(
        "All Weather Sharpe: %0.3f" % util.print_annualized_sharpe(aw_pcts.sum(axis=1))
    )

    all_weather_indexed = util.one_index(aw_pcts.sum(axis=1).dropna())
    benchmark_indexed = util.one_index(
        benchmark_pcts[benchmark_pcts.columns[0]].dropna()
    )

    all_weather_indexed["All Weather"] = all_weather_indexed["Value"]
    benchmark_indexed["Benchmark"] = benchmark_indexed["Value"]
    del all_weather_indexed["Value"]
    del benchmark_indexed["Value"]

    total = all_weather_indexed.join(benchmark_indexed)
    print("Output backtest results to: %s" % out)
    total.dropna().to_csv(out)

    print("\nWeights for today:")
    weights = all_weather.optimize()
    for key in weights.keys():
        print(key, "\t\t", weights[key]["weight"])


if __name__ == "__main__":
    all_weather()
