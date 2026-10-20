# -*- coding: utf-8 -*-

import os
import sys
import unittest

sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from test_api import InvenTreeTestCase  # noqa: E402

import inventree.part  # noqa: E402
from inventree.part import Part  # noqa: E402
from inventree.pricing import InternalPrice, PartPricing, SalePrice  # noqa: E402


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
