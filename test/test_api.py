# -*- coding: utf-8 -*-

import unittest

import os
import sys

sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from inventree import base  # noqa: E402
from inventree import api  # noqa: E402
from inventree import part  # noqa: E402
from inventree import stock  # noqa: E402


SERVER = os.environ.get('INVENTREE_PYTHON_TEST_SERVER', 'http://127.0.0.1:8000')
USERNAME = os.environ.get('INVENTREE_PYTHON_TEST_USERNAME', 'admin')
PASSWORD = os.environ.get('INVENTREE_PYTHON_TEST_PASSWORD', 'password')


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

    def test_file_download(self):
        """
        Attemtping to download a file while unauthenticated should return False
        """

        self.assertFalse(self.api.downloadFile('/media/part/files/1/test.pdf', 'test.pdf'))


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

        self.assertIn('apiVersion', details)
        
        api_version = int(details['apiVersion'])

        self.assertTrue(api_version >= self.api.getMinApiVersion())


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

        n = len(tests)
        self.assertGreater(n, 0)

        # Upload a test result against 'firmware' (should fail the first time)
        args = {
            'attachment': 'test/attachment.txt',
            'value': '0x123456',
        }

        result = item.uploadTestResult('firmware', False, **args)

        self.assertTrue(result)

        item.uploadTestResult('paint', True)
        item.uploadTestResult('extra test', False, value='some data')

        # There should be 3 more test results now!
        results = item.getTestResults()
        self.assertEqual(len(results), n + 3)


if __name__ == '__main__':
    print("Running InvenTree Python Unit Tests: Version " + base.INVENTREE_PYTHON_VERSION)
    unittest.main()
