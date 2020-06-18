import pandas as pd
import numpy as np


def one_index(series: pd.Series, use_ln=False) -> pd.DataFrame:
    values = [1]
    for i, pct_change in series.iteritems():
        if len(values) > 1:
            values.append(
                {
                    "Date": i,
                    "Value": values[-1]["Value"] * (1 + pct_change)
                }
            )
        else:  # first value
            values.append({
                "Date": i,
                "Value": (1 + pct_change)
            })

    df = pd.DataFrame.from_records(values[1:]).set_index("Date")
    if use_ln:
        df['Value'] = df['Value'].apply(np.log)
    return df


def print_annualized_sharpe(series: pd.Series, periodicity='daily'):
    stddev = (np.std(series) * np.sqrt(252))
    sharpe = (np.mean(series) * 252) / stddev
    return sharpe


def normalize_weights(allocations):
    exposures = []
    for name in allocations:
        tup = (name, allocations[name]['weight'])
        exposures.append(tup)

    df = pd.DataFrame(exposures, columns=['name', 'exposures'])
    df['exposures'] = df['exposures'] / df['exposures'].abs().sum()

    for name in allocations:
        weight = df[df['name'] == name]['exposures'].iloc[0]
        allocations[name]['weight'] = weight

    return allocations