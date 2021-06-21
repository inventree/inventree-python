# -*- coding: utf-8 -*-

import os
import sys

sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from inventree import stock  # noqa: E402
from inventree import part  # noqa: E402

from test_api import InvenTreeTestCase  # noqa: E402


class StockTest(InvenTreeTestCase):
    """
    Test alternative ways of getting StockItem objects.
    """

    def test_stock(self):

        s = stock.StockItem.list(self.api, part=1)
        self.assertEqual(len(s), 2)

        s = part.Part(self.api, 1).getStockItems()
        self.assertEqual(len(s), 2)
        
    def test_get_stock_item(self):

        item = stock.StockItem(self.api, pk=1)

        self.assertEqual(item.pk, 1)
        self.assertEqual(item.location, 4)

        # Get the Part reference
        prt = item.getPart()

        self.assertEqual(type(prt), part.Part)
        self.assertEqual(prt.pk, 1)

        # Get the Location reference
        location = item.getLocation()

        self.assertEqual(type(location), stock.StockLocation)
        self.assertEqual(location.pk, 4)
        self.assertEqual(location.name, "Electronic Component Storage")


class StockLocationTest(InvenTreeTestCase):
    """
    Tests for the StockLocation model
    """

    def test_location_list(self):
        locs = stock.StockLocation.list(self.api)
        self.assertEqual(len(locs), 4)

        for loc in locs:
            self.assertEqual(type(loc), stock.StockLocation)

    def test_location_stock(self):

        location = stock.StockLocation(self.api, pk=4)

        self.assertEqual(location.pk, 4)
        self.assertEqual(location.description, "Storage for electronic components")

        items = location.getStockItems()

        self.assertEqual(len(items), 3)

        items = location.getStockItems(part=1)
        self.assertEqual(len(items), 2)

        items = location.getStockItems(part=5)
        self.assertEqual(len(items), 1)

    def test_location_parent(self):
        """
        Return the Parent location
        """

        location = stock.StockLocation(self.api, pk=4)
        self.assertEqual(location.parent, 1)

        parent = location.getParentLocation()

        self.assertEqual(type(parent), stock.StockLocation)
        self.assertEqual(parent.pk, 1)
        self.assertIsNone(parent.parent)
        self.assertIsNone(parent.getParentLocation())

        children = parent.getChildLocations()
        self.assertEqual(len(children), 2)

        for child in children:
            self.assertEqual(type(child), stock.StockLocation)
            self.assertEqual(child.parent, parent.pk)
