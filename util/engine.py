import abc


class Engine(object):
    """
    Abstract class for modules that
    retrieve raw data from data sources.
    """
    __metaclass__ = abc.ABCMeta
    config = None

    @abc.abstractmethod
    def get(self, symbol):
        pass

    @abc.abstractproperty
    def config(self):
        return self.config
