# -*- coding: utf-8 -*-

import unittest

import sys
sys.path.append(".")

from inventree import base  # noqa: E402
from inventree import api  # noqa: E402
from inventree import part  # noqa: E402
from inventree import stock  # noqa: E402
from inventree import company  # noqa: E402


SERVER = "http://127.0.0.1:8000"
USERNAME = "admin"
PASSWORD = "password"


class LoginTests(unittest.TestCase):

    def test_failed_logins(self):

        # Attempt connection where no server exists
        with self.assertRaises(Exception):
            a = api.InvenTreeAPI("http://127.0.0.1:1234", username="admin", password="password")

        # Attempt connection with invalid credentials
        a = api.InvenTreeAPI(SERVER, username="abcde", password="********")

        self.assertIsNotNone(a.server_details)
        self.assertIsNone(a.token)


class Unauthenticated(unittest.TestCase):
    """
    Test that we cannot access the data if we are not authenticated.
    """

    def setUp(self):
        self.api = api.InvenTreeAPI(SERVER, username="hello", password="world")

    def test_read_parts(self):
        parts = part.Part.list(self.api)

        self.assertEqual(len(parts), 0)


class InvenTreeTestCase(unittest.TestCase):

    def setUp(self):
        """
        Test case setup functions
        """
        self.api = api.InvenTreeAPI(SERVER, username=USERNAME, password=PASSWORD)


class InvenTreeAPITest(InvenTreeTestCase):

    def test_token(self):
        self.assertIsNotNone(self.api.token)

    def test_details(self):
        self.assertIsNotNone(self.api.server_details)

        details = self.api.server_details
        self.assertIn('server', details)
        self.assertIn('instance', details)


class PartTest(InvenTreeTestCase):
    """
    Test for PartCategory and Part objects.
    """

    def test_part_cats(self):

        cats = part.Part.list(self.api)
        self.assertEqual(len(cats), 8)

    def test_elec(self):
        electronics = part.PartCategory(self.api, 1)

        # This is a top-level category, should not have a parent!
        self.assertIsNone(electronics.getParentCategory())
        self.assertEqual(electronics.name, "Electronics")

        children = electronics.getChildCategories()
        self.assertEqual(len(children), 1)
        
        passives = children[0]
        self.assertEqual(passives.name, 'Passives')
        
        # Grab all child categories
        children = part.PartCategory.list(self.api, parent=passives.pk)
        self.assertEqual(len(children), 3)

        children = passives.getChildCategories()
        self.assertEqual(len(children), 3)
        
        parent = passives.getParentCategory()
        self.assertEqual(parent.pk, 1)
        self.assertEqual(parent.name, 'Electronics')
        
    def test_caps(self):

        # Capacitors
        capacitors = part.PartCategory(self.api, 6)
        self.assertEqual(capacitors.name, "Capacitors")
        parts = capacitors.getParts()
        self.assertEqual(len(parts), 4)

        for p in parts:
            self.assertEqual(p.category, capacitors.pk)

    def test_parts(self):

        parts = part.Part.list(self.api)
        self.assertEqual(len(parts), 8)

        parts = part.Part.list(self.api, category=5)
        self.assertEqual(len(parts), 3)


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


class TestCreate(InvenTreeTestCase):
    """
    Test that objects can be created via the API
    """

    def test_create_stuff(self):

        # Create a custom category
        c = part.PartCategory.create(self.api, {
            'parent': None,
            'name': 'My custom category',
            'description': 'A part category',
        })

        self.assertIsNotNone(c)
        self.assertIsNotNone(c.pk)

        p = part.Part.create(self.api, {
            'name': 'ACME Widget',
            'description': 'A simple widget created via the API',
            'category': c.pk,
            'ipn': 'ACME-0001',
            'virtual': False,
            'active': True
        })

        self.assertIsNotNone(p)
        self.assertEqual(p.category, c.pk)

        cat = p.getCategory()
        self.assertEqual(cat.pk, c.pk)
        self.assertEqual(cat.name, 'My custom category')

        s = stock.StockItem.create(self.api, {
            'part': p.pk,
            'quantity': 45,
            'notes': 'This is a note',

        })

        self.assertIsNotNone(s)
        self.assertEqual(s.part, p.pk)

        prt = s.getPart()
        self.assertEqual(prt.pk, p.pk)
        self.assertEqual(prt.name, 'ACME Widget')


class WidgetTest(InvenTreeTestCase):

    def test_get_widget(self):

        widget = part.Part(self.api, 8)
        self.assertEqual(widget.IPN, "W001")

        test_templates = widget.getTestTemplates()
        self.assertEqual(len(test_templates), 3)
        
        keys = [test.key for test in test_templates]

        self.assertIn('firmware', keys)
        self.assertIn('weight', keys)
        self.assertIn('paint', keys)

    def test_add_result(self):
        
        # Look for a particular serial number
        item = stock.StockItem.list(self.api, IPN="W001", serial=10)
        self.assertEqual(len(item), 1)
        item = item[0]

        tests = item.getTestResults()
        self.assertEqual(len(tests), 1)

        # Upload a test result against 'firmware' (should fail the first time)
        args = {
            'attachment': 'test/attachment.txt',
            'value': '0x123456',
        }

        result = item.uploadTestResult('firmware', False, **args)

        self.assertTrue(result)

        item.uploadTestResult('paint', True)
        item.uploadTestResult('extra test', False, value='some data')

        results = item.getTestResults()
        self.assertEqual(len(results), 4)


class CompanyTest(InvenTreeTestCase):
    """
    Test that Company related objects can be managed via the API
    """

    def test_company_create(self):
        c = company.Company(self.api, {
            'name': 'Company',
        })

        self.assertIsNotNone(c)

    def test_manufacturer_part_create(self):
        manufacturer = company.Company(self.api, 1)

        manufacturer_part = company.ManufacturerPart(self.api, {
            'manufacturer': manufacturer,
            'MPN': 'MPN_TEST',
        })

        self.assertIsNotNone(manufacturer_part)

    def test_supplier_part_create(self):
        supplier = company.Company(self.api, 1)

        supplier_part = company.SupplierPart(self.api, {
            'manufacturer': supplier,
            'SKU': 'SKU_TEST',
        })

        self.assertIsNotNone(supplier_part)


if __name__ == '__main__':
    print("Running InvenTree Python Unit Tests: Version " + base.INVENTREE_PYTHON_VERSION)
    unittest.main()
