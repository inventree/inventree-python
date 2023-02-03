"""Manages currency / conversion support for InvenTree"""


import logging


logger = logging.getLogger('inventree')


class CurrencyManger(object):
    """Class for managing InvenTree currency suppport"""

    # Currency API introduced v92
    REQUIRED_API_VERSION = 92

    # Currency API endpoint
    CURRENCY_ENDPOINT = 'currency/exchange/'

    def __init__(self, api):
        """Construct a CurrencyManager instance"""

        # Store internal reference to the API
        self.api = api

        self.base_currency = None
        self.exchange_rates = None
    
    def updateFromServer(self):
        """Retrieve currency data from the server"""

        if self.api.api_version < self.REQUIRED_API_VERSION:
            raise ValueError(f"Server API version ({self.api.api_version}) is older than {self.REQUIRED_API_VERSION}, which is required for currency support")

        response = self.api.get(self.CURRENCY_ENDPOINT)

        if response is None:
            logger.error("Could not retrieve currency data from InvenTree server")
            return
        
        self.base_currency = response.get('base_currency', None)
        self.exchange_rates = response.get('exchange_rates', None)

        if self.base_currency is None:
            logger.warning("'base_currency' missing from server response")
        
        if self.exchange_rates is None:
            logger.warning("'exchange_rates' missing from server response")

    def getBaseCurrency(self, cache=True):
        """Return the base currency code (e.g. 'USD') from the server"""

        if not cache or not self.base_currency:
            self.updateFromServer()
        
        return self.base_currency
    
    def getExchangeRates(self, cache=True):
        """Return the exchange rate information from the server"""

        if not cache or not self.exchange_rates:
            self.updateFromServer()
        
        return self.exchange_rates

