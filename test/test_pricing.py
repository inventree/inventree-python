# -*- coding: utf-8 -*-

import os
import sys
import unittest

sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from test_api import InvenTreeTestCase  # noqa: E402

import inventree.part  # noqa: E402
from inventree.part import Part  # noqa: E402
from inventree.pricing import (  # noqa: E402
    STOCK_COST_API_VERSION,
    CostType,
    InternalPrice,
    PartPricing,
    SalePrice,
    StockItemCost,
    StockItemCostEntry,
)
from inventree.stock import StockItem  # noqa: E402


class DummyAPI:
    """Minimal stand-in for InvenTreeAPI, providing only the API version"""

    def __init__(self, api_version):
        self.api_version = api_version


class PricingURLTests(unittest.TestCase):
    """Test that pricing model URLs are determined by the server API version"""

    def test_backwards_compatible_imports(self):
        """Pricing models can still be imported from inventree.part"""

        self.assertIs(inventree.part.InternalPrice, InternalPrice)
        self.assertIs(inventree.part.SalePrice, SalePrice)
        self.assertIs(inventree.part.PartPricing, PartPricing)

    def test_urls(self):
        """Legacy URLs are used for older servers, new URLs otherwise"""

        expected = {
            InternalPrice: ('part/internal-price/', 'pricing/internal-price/'),
            SalePrice: ('part/sale-price/', 'pricing/sale-price/'),
        }

        for cls, (legacy_url, new_url) in expected.items():
            version = cls.PRICING_API_VERSION

            self.assertEqual(cls.get_url(DummyAPI(version - 1)), legacy_url)
            self.assertEqual(cls.get_url(DummyAPI(version)), new_url)
            self.assertEqual(cls.get_url(DummyAPI(version + 1)), new_url)

            # No API (or unknown version) defaults to the new URL
            self.assertEqual(cls.get_url(), new_url)
            self.assertEqual(cls.get_url(None), new_url)

    def test_instance_url(self):
        """Instance URL is constructed from the version-specific base URL"""

        data = {'pk': 3, 'part': 1, 'quantity': 1, 'price': '1.00'}

        legacy = InternalPrice(DummyAPI(InternalPrice.PRICING_API_VERSION - 1), data=data)
        self.assertTrue(legacy._url.startswith('part/internal-price/'))

        new = InternalPrice(DummyAPI(InternalPrice.PRICING_API_VERSION), data=data)
        self.assertTrue(new._url.startswith('pricing/internal-price/'))


class PartPricingOfflineTests(unittest.TestCase):
    """Unit tests for the PartPricing class which do not require a server"""

    DATA = {'overall_min': '1.00', 'overall_max': '2.00'}

    def test_detail_url(self):
        """Pricing URL is determined by the server API version"""

        version = PartPricing.PRICING_API_VERSION

        self.assertEqual(PartPricing.get_detail_url(DummyAPI(version - 1), 7), 'part/7/pricing/')
        self.assertEqual(PartPricing.get_detail_url(DummyAPI(version), 7), 'pricing/part/7/')
        self.assertEqual(PartPricing.get_detail_url(None, 7), 'pricing/part/7/')

        legacy = PartPricing(DummyAPI(version - 1), part=7, data=self.DATA)
        self.assertEqual(legacy._url, 'part/7/pricing/')

        new = PartPricing(DummyAPI(version), part=7, data=self.DATA)
        self.assertEqual(new._url, 'pricing/part/7/')

    def test_part_reference(self):
        """PartPricing is identified by the linked part"""

        class DummyPart:
            pk = 12

        for part in [12, '12', DummyPart()]:
            pricing = PartPricing(None, part=part, data=self.DATA)
            self.assertEqual(pricing.pk, 12)
            self.assertTrue(pricing.is_valid())
            self.assertEqual(pricing.overall_min, '1.00')

        with self.assertRaises(TypeError):
            PartPricing(None, part='abc', data=self.DATA)

        for part in [0, -1]:
            with self.assertRaises(ValueError):
                PartPricing(None, part=part, data=self.DATA)

    def test_unsupported(self):
        """Operations not supported by the pricing endpoint raise an error"""

        api = DummyAPI(PartPricing.PRICING_API_VERSION)

        with self.assertRaises(NotImplementedError):
            PartPricing.list(api)

        with self.assertRaises(NotImplementedError):
            PartPricing.count(api)

        with self.assertRaises(NotImplementedError):
            PartPricing.create(api, {})

        with self.assertRaises(NotImplementedError):
            PartPricing.options(api)

        with self.assertRaises(NotImplementedError):
            PartPricing(api, part=1, data=self.DATA).delete()


class InternalPriceTest(InvenTreeTestCase):
    """ Test that the InternalPrice related objects can be managed via the API """

    def test_fields(self):
        """
        Test field names via OPTIONS request
        """

        field_names = InternalPrice.fieldNames(self.api)

        for field in [
            'part',
            'quantity',
            'price'
        ]:
            self.assertIn(field, field_names)

    def test_internal_price_create(self):
        """
        Tests the ability to create an internal price
        """
        p = Part.create(self.api, {
            'name': 'Test Part',
            'description': 'Test Part',
            'category': 1,
            'revision': 1,
            'active': True,
        })

        self.assertIsNotNone(p)
        self.assertIsNotNone(p.pk)

        ip = InternalPrice.create(self.api, {
            'part': p.pk,
            'quantity': 1,
            'price': '1.00'
        })

        self.assertIsNotNone(ip)


class SalePriceTest(InvenTreeTestCase):
    """Test that the SalePrice related objects can be managed via the API"""

    def test_fields(self):
        """Test field names via OPTIONS request"""

        field_names = SalePrice.fieldNames(self.api)

        for field in [
            'part',
            'quantity',
            'price',
            'price_currency',
        ]:
            self.assertIn(field, field_names)

    def test_set_sale_price(self):
        """Test that a sale price can be set and retrieved for a part"""

        p = Part.list(self.api, salable=True)[0]

        # Delete any existing sale prices
        for price in SalePrice.list(self.api, part=p.pk):
            self.assertEqual(type(price), SalePrice)
            price.delete()

        self.assertEqual(len(SalePrice.list(self.api, part=p.pk)), 0)

        SalePrice.setSalePrice(self.api, p.pk, 1, 12.5, 'USD')

        prices = SalePrice.list(self.api, part=p.pk)
        self.assertEqual(len(prices), 1)
        self.assertEqual(prices[0].part, p.pk)
        self.assertEqual(float(prices[0].price), 12.5)
        self.assertEqual(float(p.getSalePrice()), 12.5)


class PartPricingTest(InvenTreeTestCase):
    """Test that PartPricing data can be accessed via the API"""

    def test_get_pricing(self):
        """Pricing data can be retrieved for a part"""

        p = Part.list(self.api)[0]

        pricing = p.getPricing()

        self.assertEqual(type(pricing), PartPricing)
        self.assertEqual(pricing.pk, p.pk)
        self.assertTrue(pricing.is_valid())

        for field in [
            'overall_min',
            'overall_max',
            'internal_cost_min',
            'internal_cost_max',
            'override_min',
            'override_max',
        ]:
            self.assertIn(field, pricing)

    def test_update_pricing(self):
        """A pricing update can be requested for a part"""

        p = Part.list(self.api)[0]

        pricing = PartPricing(self.api, part=p)

        response = pricing.updatePricing()

        self.assertIsNotNone(response)
        self.assertTrue(pricing.is_valid())

        pricing.reload()
        self.assertTrue(pricing.is_valid())


class RecordingAPI(DummyAPI):
    """Stand-in for InvenTreeAPI which records requests, and returns canned responses"""

    def __init__(self, api_version, response=None):
        super().__init__(api_version)
        self.response = response
        self.requests = []

    def get(self, url, params=None, **kwargs):
        self.requests.append(('GET', url, params))
        return self.response

    def post(self, url, data, **kwargs):
        self.requests.append(('POST', url, data))
        return {'pk': 1, **data}


class StockItemCostOfflineTests(unittest.TestCase):
    """Unit tests for the stock item cost models which do not require a server"""

    VERSION = STOCK_COST_API_VERSION

    def test_api_version(self):
        """Stock item cost models require the matching server API version"""

        old = RecordingAPI(self.VERSION - 1)
        new = RecordingAPI(self.VERSION, response=[])

        for cls in [StockItemCostEntry, StockItemCost]:
            self.assertEqual(cls.MIN_API_VERSION, self.VERSION)

            with self.assertRaises(NotImplementedError):
                cls.list(old)

            self.assertEqual(cls.list(new), [])

        item = StockItem(old, data={'pk': 5})

        with self.assertRaises(NotImplementedError):
            item.getCostEntries()

        with self.assertRaises(NotImplementedError):
            item.getCost()

        with self.assertRaises(NotImplementedError):
            item.addCostEntry(cost=1)

        with self.assertRaises(NotImplementedError):
            StockItemCostEntry.getCostTypes(old)

        # No request is made to an unsupported server
        self.assertEqual(old.requests, [])

    def test_urls(self):
        """Stock item cost models use the pricing app URLs"""

        api = DummyAPI(self.VERSION)

        self.assertEqual(StockItemCostEntry.get_url(api), 'pricing/stock-cost-entry/')
        self.assertEqual(StockItemCost.get_url(api), 'pricing/stock-cost/')

    def test_add_cost(self):
        """Cost entry data is constructed from the provided arguments"""

        api = RecordingAPI(self.VERSION)
        item = StockItem(api, data={'pk': 5})

        entry = item.addCostEntry(cost='1.5', currency='AUD', notes='Freight')

        self.assertEqual(type(entry), StockItemCostEntry)
        self.assertEqual(api.requests[-1], ('POST', 'pricing/stock-cost-entry/', {
            'stock_item': 5,
            'cost_type': CostType.PURCHASE,
            'min_cost': '1.5',
            'max_cost': '1.5',
            'currency': 'AUD',
            'notes': 'Freight',
        }))

        # Cost range, with only a single bound (server fills in the other bound)
        StockItemCostEntry.addCost(api, 7, CostType.LANDED, min_cost=2)

        self.assertEqual(api.requests[-1], ('POST', 'pricing/stock-cost-entry/', {
            'stock_item': 7,
            'cost_type': CostType.LANDED,
            'min_cost': 2,
        }))

        with self.assertRaises(ValueError):
            item.addCostEntry()

        with self.assertRaises(ValueError):
            item.addCostEntry(cost=1, min_cost=1)

    def test_cost_summary(self):
        """The cost summary is looked up by stock item, and is read-only"""

        api = RecordingAPI(self.VERSION, response=[])
        item = StockItem(api, data={'pk': 5})

        # No cost data for this stock item
        self.assertIsNone(item.getCost())
        self.assertEqual(api.requests[-1], ('GET', 'pricing/stock-cost/', {'stock_item': 5}))

        api.response = [{'pk': 9, 'stock_item': 5, 'currency': 'USD', 'min_cost': '1.0', 'max_cost': '2.0', 'incomplete': False}]

        summary = item.getCost()

        self.assertEqual(type(summary), StockItemCost)
        self.assertEqual(summary.pk, 9)
        self.assertEqual(summary.stock_item, 5)

        with self.assertRaises(NotImplementedError):
            StockItemCost.create(api, {})

        with self.assertRaises(NotImplementedError):
            summary.save()

        with self.assertRaises(NotImplementedError):
            summary.delete()


class StockItemCostTest(InvenTreeTestCase):
    """Test that stock item cost data can be managed via the API"""

    def setUp(self):
        super().setUp()

        if self.api.api_version < STOCK_COST_API_VERSION:
            self.skipTest(f"Stock item costs require API version >= {STOCK_COST_API_VERSION}")

    def test_fields(self):
        """Test field names via OPTIONS request"""

        field_names = StockItemCostEntry.fieldNames(self.api)

        for field in ['stock_item', 'cost_type', 'currency', 'min_cost', 'max_cost', 'notes']:
            self.assertIn(field, field_names)

    def test_cost_types(self):
        """Cost type definitions match the values provided by the server"""

        data = StockItemCostEntry.getCostTypes(self.api)
        values = {v['key']: v['name'] for v in data['values'].values()}

        self.assertEqual(values[CostType.PURCHASE], 'PURCHASE')
        self.assertEqual(values[CostType.OTHER], 'OTHER')

    def test_stock_item_costs(self):
        """Cost entries can be created, edited and removed, and are reflected in the summary"""

        item = StockItem.list(self.api, limit=1)[0]

        # Remove any existing cost entries
        for entry in item.getCostEntries():
            entry.delete()

        self.assertEqual(len(item.getCostEntries()), 0)
        self.assertIsNone(item.getCost())

        purchase = item.addCostEntry(cost=10, currency='USD')
        item.addCostEntry(CostType.LANDED, min_cost=1, max_cost=3, currency='USD', notes='Freight')

        entries = item.getCostEntries()
        self.assertEqual(len(entries), 2)

        for entry in entries:
            self.assertEqual(type(entry), StockItemCostEntry)
            self.assertEqual(entry.stock_item, item.pk)
            self.assertEqual(entry.getStockItem().pk, item.pk)

        self.assertEqual(len(item.getCostEntries(cost_type=CostType.LANDED)), 1)

        # Edit an existing entry
        purchase.save({'min_cost': 12, 'max_cost': 12})
        self.assertEqual(float(purchase.min_cost), 12)

        summary = item.getCost()

        self.assertEqual(type(summary), StockItemCost)
        self.assertEqual(summary.getStockItem().pk, item.pk)

        if summary.currency == 'USD':
            self.assertEqual(float(summary.min_cost), 13)
            self.assertEqual(float(summary.max_cost), 15)

        # Removing all entries removes the summary
        for entry in item.getCostEntries():
            entry.delete()

        self.assertIsNone(item.getCost())
