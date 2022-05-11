# -*- coding: utf-8 -*-

import os
import sys

sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from inventree.stock import StockItem, StockLocation  # noqa: E402
from inventree import part  # noqa: E402

from test_api import InvenTreeTestCase  # noqa: E402


class StockLocationTest(InvenTreeTestCase):
    """
    Tests for the StockLocation model

    Fixture data can be found in the InvenTree source:
    
    - InvenTree/stock/fixtures/location.yaml

    """

    def test_location_list(self):
        """
        Test the LIST API endpoint for the StockLocation model
        """
        
        locs = StockLocation.list(self.api)
        self.assertGreaterEqual(len(locs), 4)

        for loc in locs:
            self.assertEqual(type(loc), StockLocation)

    def test_location_create(self):
        """
        Check that we can create a new stock location via the APi
        """

        n = len(StockLocation.list(self.api))

        parent = StockLocation(self.api, pk=7)

        n_childs = len(parent.getChildLocations())

        # Create a sublocation with a unique name
        location = StockLocation.create(
            self.api,
            {
                "name": f"My special location {n_childs}",
                "description": "A location created with the API!",
                "parent": 7
            }
        )

        self.assertIsNotNone(location)

        # Now, request back via the API using a secondary object
        loc = StockLocation(self.api, pk=location.pk)

        self.assertEqual(loc.name, f"My special location {n_childs}")
        self.assertEqual(loc.parent, 7)

        # Change the name of the location
        loc.save({
            "name": f"A whole new name {n_childs}",
        })

        # Reload the original object
        location.reload()

        self.assertEqual(location.name, f"A whole new name {n_childs}")

        # Check that the number of locations has been updated
        locs = StockLocation.list(self.api)
        self.assertEqual(len(locs), n + 1)

    def test_location_stock(self):
        """Query stock by location"""
        location = StockLocation(self.api, pk=4)

        self.assertEqual(location.pk, 4)
        self.assertEqual(location.description, "Place of work")

        items = location.getStockItems()

        self.assertGreaterEqual(len(items), 20)

        # Check specific part stock in location 1 (initially empty)
        items = location.getStockItems(part=1)

        n = len(items)

        for i in range(5):
            StockItem.create(
                self.api,
                {
                    "part": 1,
                    "quantity": (i + 1) * 50,
                    "location": location.pk,
                }
            )
        
            items = location.getStockItems(part=1)
            self.assertEqual(len(items), n + i + 1)

        items = location.getStockItems(part=5)
        self.assertGreaterEqual(len(items), 1)

        for item in items:
            self.assertEqual(item.location, location.pk)
            self.assertEqual(item.part, 5)

    def test_location_parent(self):
        """
        Return the Parent location
        """

        # This location does not have a parent
        location = StockLocation(self.api, pk=4)
        self.assertIsNone(location.parent)
        parent = location.getParentLocation()

        self.assertIsNone(parent)

        # Now, get a location which *does* have a parent
        location = StockLocation(self.api, pk=7)
        self.assertIsNotNone(location.parent)
        self.assertEqual(location.parent, 4)

        parent = location.getParentLocation()

        self.assertEqual(type(parent), StockLocation)
        self.assertEqual(parent.pk, 4)
        self.assertIsNone(parent.parent)
        self.assertIsNone(parent.getParentLocation())

        children = parent.getChildLocations()
        self.assertGreaterEqual(len(children), 2)

        for child in children:
            self.assertEqual(type(child), StockLocation)
            self.assertEqual(child.parent, parent.pk)


class StockTest(InvenTreeTestCase):
    """
    Test alternative ways of getting StockItem objects.

    Fixture data can be found in the InvenTree source:
    
    - InvenTree/stock/fixtures/stock.yaml
    """

    def test_stock(self):

        items = StockItem.list(self.api, part=1)

        n = len(items)

        self.assertGreaterEqual(n, 2)

        for item in items:
            self.assertEqual(item.part, 1)

        # Request via the Part instance (results should be the same!)
        items = part.Part(self.api, 1).getStockItems()
        self.assertEqual(len(items), n)
        
    def test_get_stock_item(self):
        """
        StockItem API tests.
        
        Refer to fixture data in InvenTree/stock/fixtures/stock.yaml
        """

        item = StockItem(self.api, pk=1)

        self.assertEqual(item.pk, 1)
        self.assertEqual(item.location, 3)

        # Get the Part reference
        prt = item.getPart()

        self.assertEqual(type(prt), part.Part)
        self.assertEqual(prt.pk, 1)

        # Get the Location reference
        location = item.getLocation()

        self.assertEqual(type(location), StockLocation)
        self.assertEqual(location.pk, 3)
        self.assertEqual(location.name, "Dining Room")
