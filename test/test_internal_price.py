# -*- coding: utf-8 -*-

import os
import sys

sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from test_api import InvenTreeTestCase  # noqa: E402

from inventree.part import InternalPrice, Part  # noqa: E402


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
