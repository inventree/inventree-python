# -*- coding: utf-8 -*-

import os
import sys

import requests

sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from test_api import InvenTreeTestCase  # noqa: E402

from inventree import company  # noqa: E402
from inventree import part  # noqa: E402
from inventree.stock import StockItem, StockLocation  # noqa: E402


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

        self.assertGreaterEqual(len(items), 15)

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

        # Grab the first available stock item
        item = StockItem.list(self.api, in_stock=True, limit=1)[0]

        # Get the Part reference
        prt = item.getPart()

        self.assertEqual(type(prt), part.Part)

        # Move the item to a known location
        item.transferStock(3)
        item.reload()

        location = item.getLocation()

        self.assertEqual(type(location), StockLocation)
        self.assertEqual(location.pk, 3)
        self.assertEqual(location.name, "Dining Room")

    def test_bulk_delete(self):
        """Test bulk deletion of stock items"""

        # Add some items to location 3
        for i in range(10):
            StockItem.create(self.api, {
                'location': 3,
                'part': 1,
                'quantity': i + 50,
            })

        self.assertTrue(len(StockItem.list(self.api, location=3)) >= 10)

        # Delete *all* items from location 3
        StockItem.bulkDelete(self.api, filters={
            'location': 3
        })

        loc = StockLocation(self.api, pk=3)
        items = loc.getStockItems()
        self.assertEqual(len(items), 0)

    def test_barcode_support(self):
        """Test barcode support for the StockItem model"""

        items = StockItem.list(self.api, limit=10)

        for item in items:
            # Delete any existing barcode
            item.unassignBarcode()

            # Perform lookup based on 'internal' barcode
            response = self.api.scanBarcode(
                {
                    "stockitem": item.pk,
                }
            )

            self.assertEqual(response['stockitem']['pk'], item.pk)
            self.assertEqual(response['plugin'], 'InvenTreeBarcode')

            # Assign a custom barcode to this StockItem
            barcode = f"custom-stock-item-{item.pk}"
            item.assignBarcode(barcode)

            response = self.api.scanBarcode(barcode)

            self.assertEqual(response['stockitem']['pk'], item.pk)
            self.assertEqual(response['plugin'], 'InvenTreeBarcode')
            self.assertEqual(response['barcode_data'], barcode)

            item.unassignBarcode()


class StockAdjustTest(InvenTreeTestCase):
    """Unit tests for stock 'adjustment' actions"""

    def test_count(self):
        """Test the 'count' action"""

        # Find the first available stock item
        item = StockItem.list(self.api, in_stock=True, limit=1)[0]

        # Count number of tracking entries
        n_tracking = len(item.getTrackingEntries())

        q = item.quantity

        item.countStock(q + 100)
        item.reload()

        self.assertEqual(item.quantity, q + 100)

        item.countStock(q, notes='Why hello there')
        item.reload()
        self.assertEqual(item.quantity, q)

        # 2 tracking entries should have been added
        self.assertEqual(
            len(item.getTrackingEntries()),
            n_tracking + 2
        )

        # The most recent tracking entry should have a note
        t = item.getTrackingEntries()[0]
        self.assertEqual(t.label, 'Stock counted')

        # Check error conditions
        with self.assertRaises(requests.exceptions.HTTPError):
            item.countStock('not a number')

        with self.assertRaises(requests.exceptions.HTTPError):
            item.countStock(-1)

    def test_add_remove(self):
        """Test the 'add' and 'remove' actions"""

        # Find the first available stock item
        item = StockItem.list(self.api, in_stock=True, limit=1)[0]

        n_tracking = len(item.getTrackingEntries())

        q = item.quantity

        # Add some items
        item.addStock(10)
        item.reload()
        self.assertEqual(item.quantity, q + 10)

        # Remove the items again
        item.removeStock(10)
        item.reload()
        self.assertEqual(item.quantity, q)

        # 2 additional tracking entries should have been added
        self.assertTrue(len(item.getTrackingEntries()) > n_tracking)

        # Test error conditions
        for v in [-1, 'gg', None]:
            with self.assertRaises(requests.exceptions.HTTPError):
                item.addStock(v)
            with self.assertRaises(requests.exceptions.HTTPError):
                item.removeStock(v)

    def test_transfer(self):
        """Unit test for 'transfer' action"""

        item = StockItem(self.api, pk=2)

        n_tracking = len(item.getTrackingEntries())

        # Transfer to a StockLocation instance
        location = StockLocation(self.api, pk=1)

        item.transferStock(location)
        item.reload()
        self.assertEqual(item.location, 1)

        # Transfer with a location ID
        item.transferStock(2)
        item.reload()
        self.assertEqual(item.location, 2)

        # 2 additional tracking entries should have been added
        self.assertTrue(len(item.getTrackingEntries()) > n_tracking)

        # Attempt to transfer to an invalid location
        for loc in [-1, 'qqq', 99999, None]:
            with self.assertRaises(requests.exceptions.HTTPError):
                item.transferStock(loc)

        # Attempt to transfer with an invalid quantity
        for q in [-1, None, 'hhhh']:
            with self.assertRaises(requests.exceptions.HTTPError):
                item.transferStock(loc, quantity=q)

    def test_transfer_multiple(self):
        """Test transfer of *multiple* items"""

        items = StockItem.list(self.api, in_stock=True, location=1)

        self.assertTrue(len(items) > 1)

        # Construct data to send
        data = []

        for item in items:
            data.append({
                'pk': item.pk,
                'quantity': item.quantity,
            })

        # Transfer all items into a new location
        StockItem.transferStockItems(self.api, data, 2)

        for item in items:
            item.reload()
            self.assertEqual(item.location, 2)

        # Transfer back to the original location
        StockItem.transferStockItems(self.api, data, 1)

        for item in items:
            item.reload()
            self.assertEqual(item.location, 1)

            history = item.getTrackingEntries()

            self.assertTrue(len(history) >= 2)
            self.assertEqual(history[0].label, 'Location changed')

    def test_assign_stock(self):
        """Test assigning stock to customer"""

        items = StockItem.list(self.api)
        self.assertTrue(len(items) > 1)

        # Get first Company which is a customer
        customer = company.Company.list(self.api, is_customer=True)[0]

        # Get first part which is salable
        assignpart = part.Part.list(self.api, salable=True)[0]

        # Create stock item which can be assigned
        assignitem = StockItem.create(
            self.api,
            {
                "part": assignpart.pk,
                "quantity": 10,
            }
        )

        # Assign the item
        assignitem.assignStock(customer=customer, notes='Sell on the side')

        # Reload the item
        assignitem.reload()

        # Check the item is assigned
        self.assertTrue(assignitem.customer == customer.pk)

    def test_install_stock(self):
        """Test install and uninstall a stock item from another"""

        items = StockItem.list(self.api, available=True)

        self.assertTrue(len(items) > 1)

        # get a parent and a child part
        parent_part = part.Part.list(
            self.api,
            trackable=True,
            assembly=True,
            has_stock=True
        )[0]
        parent_stock = parent_part.getStockItems()[0]
        child_stock = items[0]
        child_part = child_stock.getPart()

        # make sure the child is in the bom of the parent

        items = parent_part.getBomItems(search=child_part.name)
        if not items:
            part.BomItem.create(
                self.api, {
                    'part': parent_part.pk,
                    'sub_part': child_part.pk,
                    'quantity': 1
                }
            )

        self.assertIsNone(child_stock.belongs_to)

        # The following checks only apply to API version 148 or higher
        # Refer to the InvenTree API version notes for more information
        if self.api.api_version >= 148:
            # Attempt to install with incorrect quantity
            with self.assertRaises(requests.exceptions.HTTPError):
                parent_stock.installStock(child_stock, quantity=child_stock.quantity * 2)

            with self.assertRaises(requests.exceptions.HTTPError):
                parent_stock.installStock(child_stock, quantity=-100)

        # install the *entire* child item into the parent
        parent_stock.installStock(child_stock, quantity=child_stock.quantity)
        child_stock.reload()
        self.assertIsNotNone(child_stock.belongs_to)
        self.assertEqual(child_stock.belongs_to, parent_stock.pk)

        # and uninstall it again
        location = StockLocation.list(self.api)[0]
        child_stock.uninstallStock(location)

        # check if the location is set correctly to confirm the uninstall
        child_stock.reload()
        new_location = child_stock.getLocation()
        self.assertTrue(new_location.pk == location.pk)
