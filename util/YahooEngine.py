import datetime
from .engine import Engine
import yfinance


class YahooEngine(Engine):
    config = {
        "stock": {
            'price': 'Adj Close'
        }
    }

    @staticmethod
    def get(symbol, **kwargs):
        start_date_str = datetime.datetime(1850, 1, 1).strftime("%Y-%m-%d")
        today_str = datetime.datetime.now().strftime("%Y-%m-%d")
        start = kwargs.get('start', start_date_str)
        end = kwargs.get('end', today_str)

        df = yfinance.download(symbol, period="max")
        df = df[(df.index >= start) & (df.index <= end)]
        return df
