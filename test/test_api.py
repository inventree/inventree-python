# -*- coding: utf-8 -*-

import unittest

import sys
sys.path.append(".")

from inventree import base
from inventree import api
from inventree import part
from inventree import stock


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


class InvenTreeTestCase(unittest.TestCase):

    def setUp(self):


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

    def test_stock(self):

        s = stock.StockItem.list(self.api, part=1)
        self.assertEqual(len(s), 2)

        s = part.Part(self.api, 1).getStockItems()
        self.assertEqual(len(s), 2)
        

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

if __name__  == '__main__':
    print("Running InvenTree Python Unit Tests: Version " + base.INVENTREE_PYTHON_VERSION)
    unittest.main()