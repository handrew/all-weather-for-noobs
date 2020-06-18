"""Base class for stocks. Inherits from asset."""
from .asset import Asset


class Stock(Asset):
    """Instantiates a Stock object.
    Constructor is the same as Asset base class.
    """

    def __init__(self, symbol, name=None, source="yahoo", interval="daily"):
        if name is None:
            name = symbol

        super(Stock, self).__init__(symbol, name, "stock", source, interval)
