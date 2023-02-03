"""Manages currency / conversion support for InvenTree"""


import logging


logger = logging.getLogger('inventree')


class CurrencyManager(object):
    """Class for managing InvenTree currency suppport"""

    # Currency API endpoint
    CURRENCY_ENDPOINT = 'currency/exchange/'

    def __init__(self, api):
        """Construct a CurrencyManager instance"""

        # Store internal reference to the API
        self.api = api

        self.base_currency = None
        self.exchange_rates = None
    
    def refreshExchangeRates(self):
        """Request the server update exchange rates from external service"""

        if self.api.api_version < 93:
            raise ValueError(f"Server API version ({self.api.api_version}) is older than v93, which is required for manual exchange rate upates")

        response = self.api.post('currency/refresh/', {})

    def updateFromServer(self):
        """Retrieve currency data from the server"""

        if self.api.api_version < 92:
            raise ValueError(f"Server API version ({self.api.api_version}) is older than v92, which is required for currency support")

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

