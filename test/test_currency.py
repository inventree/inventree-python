"""Unit tests for currency exchange support"""


import os
import sys

sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from test_api import InvenTreeTestCase  # noqa: E402

from inventree.currency import CurrencyManager


class CurrencyTest(InvenTreeTestCase):
    """Tests for currency support"""

    def test_fetch_data(self):
        """Test that we can fetch currency data from the server"""

        mgr = CurrencyManager(self.api)
        mgr.updateFromServer()

        self.assertIsNotNone(mgr.base_currency)
        self.assertIsNotNone(mgr.exchange_rates)
    
    def test_base_currency(self):
        """Test call to 'getBaseCurrency'"""

        mgr = CurrencyManager(self.api)
        base = mgr.getBaseCurrency()

        self.assertEqual(base, 'USD')
        self.assertIsNotNone(mgr.exchange_rates)
    
    def test_exchange_rates(self):
        """Test call to 'getExchangeRates'"""

        mgr = CurrencyManager(self.api)
        rates = mgr.getExchangeRates()

        self.assertIsNotNone(rates)
        self.assertIsNotNone(mgr.base_currency)
