import logging
import pandas as pd
import datetime
from numbers import Number

from .YahooEngine import YahooEngine

ENGINES = {
    'yahoo': YahooEngine,
}


class TimeSeries(object):
    def __init__(self, source):
        """
        Initializes a TimeSeries object.

        @param source: str, denoting which Engine to use
        """
        self.source = source
        if source not in ENGINES:
            raise NotImplementedError(
                "Engine {} not yet implemented. Please select from {}"
                .format(source, str(ENGINES.keys()))
            )
        else:
            self.engine = ENGINES[source]

        self.data = None
        self._interval = ""

    def get(self, symbol, **kwargs):
        if pd.isnull(symbol):
            raise TypeError("Argument 'symbol' can not be nan.")

        self.data = self.engine.get(symbol, **kwargs)

        return self.data

    @property
    def interval(self):
        if self.data is not None:
            if self._interval:
                return self._interval

            self._interval = pd.infer_freq(self.data.index)
            if self._interval is None:
                # try re-setting the dates to the first day
                reindexed = pd.Series([
                    datetime.datetime(d.year, d.month, 1)
                    for d in self.data.index.to_series()
                ])
                self._interval = pd.infer_freq(reindexed)
                if (self._interval is None):
                    self._interval = ""
                    logging.info(
                        "Could not infer frequency for {} from {}".format(
                            self.symbol,
                            self.source
                        )
                    )
            return self._interval

    def get_attribute(self, attr):
        """
        Gets (uncomputed) attribute from raw data.
        Note that volatility and momentum are not attributes
        because they are computed.
        """
        return self.data[attr].to_frame(self.symbol)[self.symbol]

    def __eq__(self, other):
        if self.data is None:
            raise TypeError("""
                Equals comparison can not be done with TimeSeries
                with underlying data None.
            """)

        if isinstance(other, TimeSeries):
            return other.data.equals(other.data)

        return False

    def __mul__(self, other):
        if isinstance(other, TimeSeries):
            return self.data.multiply(other.value)
        elif isinstance(other, pd.Series):
            return self.data.multiply(other)
        elif isinstance(other, Number):
            return self.data * other
        raise TypeError("""
            Type %s cannot be multiplied with TimeSeries.
        """ % type(other))

    # makes it such that multiplication works on either side
    __rmul__ = __mul__
