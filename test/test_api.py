# -*- coding: utf-8 -*-

import unittest
import requests

import os
import sys

sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from inventree import base  # noqa: E402
from inventree import api  # noqa: E402
from inventree import part  # noqa: E402
from inventree import stock  # noqa: E402


SERVER = os.environ.get('INVENTREE_PYTHON_TEST_SERVER', 'http://127.0.0.1:12345')
USERNAME = os.environ.get('INVENTREE_PYTHON_TEST_USERNAME', 'testuser')
PASSWORD = os.environ.get('INVENTREE_PYTHON_TEST_PASSWORD', 'testpassword')


class LoginTests(unittest.TestCase):

    def test_failed_logins(self):

        # Attempt connection where no server exists
        with self.assertRaises(Exception):
            a = api.InvenTreeAPI("http://127.0.0.1:9999", username="admin", password="password")

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

        with self.assertRaises(requests.exceptions.HTTPError) as ar:
            part.Part.list(self.api)

        self.assertIn('Invalid username/password', str(ar.exception))

    def test_file_download(self):
        """
        Attemtping to download a file while unauthenticated should raise an error
        """

        # Downloading without auth = unauthorized error (401)
        with self.assertRaises(requests.exceptions.HTTPError):
            self.assertFalse(self.api.downloadFile('/media/part/files/1/test.pdf', 'test.pdf'))


class InvenTreeTestCase(unittest.TestCase):
    """
    Base class for running InvenTree unit tests.

    - Creates an authenticated API instance
    """

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


class TemplateTest(InvenTreeTestCase):

    def test_get_widget(self):

        widget = part.Part(self.api, 10000)

        self.assertEqual(widget.name, "Chair Template")

        test_templates = widget.getTestTemplates()
        self.assertGreaterEqual(len(test_templates), 5)
        
        keys = [test.key for test in test_templates]

        self.assertIn('teststrengthofchair', keys)
        self.assertIn('applypaint', keys)
        self.assertIn('attachlegs', keys)

    def test_add_template(self):
        """
        Test that we can add a test template via the API
        """

        widget = part.Part(self.api, pk=10000)

        n = len(widget.getTestTemplates())

        part.PartTestTemplate.create(self.api, {
            'part': widget.pk,
            'test_name': f"Test_Name_{n}",
            'description': 'A test or something',
            'required': True,
        })

        self.assertEqual(len(widget.getTestTemplates()), n + 1)

    def test_add_result(self):
        
        # Look for a particular serial number
        items = stock.StockItem.list(self.api, serial=1000)
        self.assertEqual(len(items), 1)

        item = items[0]

        tests = item.getTestResults()

        n = len(tests)

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
