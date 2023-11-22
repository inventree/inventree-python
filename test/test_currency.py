"""Unit tests for currency exchange support"""


import os
import sys

sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from test_api import InvenTreeTestCase  # noqa: E402

from inventree.currency import CurrencyManager  # noqa: E402


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

    def test_conversion(self):
        """Test currency conversion"""

        mgr = CurrencyManager(self.api)
        mgr.updateFromServer()

        # Override data
        mgr.base_currency = 'USD'
        mgr.exchange_rates = {
            'USD': 1.00,
            'AUD': 1.40,
            'EUR': 0.90,
            'JPY': 128
        }

        test_sets = [
            (1, 'AUD', 'USD', 0.7143),
            (1, 'EUR', 'USD', 1.1111),
            (5, 'JPY', 'AUD', 0.0547),
            (5, 'AUD', 'EUR', 3.2143),
            (1, 'USD', 'JPY', 128)
        ]

        for value, source, target, result in test_sets:
            converted = mgr.convertCurrency(value, source, target)

            self.assertEqual(result, round(converted, 4))
