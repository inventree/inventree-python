# -*- coding: utf-8 -*-

import os
import sys
import unittest

import requests

sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from inventree import api  # noqa: E402
from inventree import base  # noqa: E402
from inventree import part  # noqa: E402
from inventree import stock  # noqa: E402

SERVER = os.environ.get('INVENTREE_PYTHON_TEST_SERVER', 'http://127.0.0.1:12345')
USERNAME = os.environ.get('INVENTREE_PYTHON_TEST_USERNAME', 'testuser')
PASSWORD = os.environ.get('INVENTREE_PYTHON_TEST_PASSWORD', 'testpassword')


class URLTests(unittest.TestCase):
    """Class for testing URL functionality"""

    def test_base_url(self):
        """Test validation of URL provided to InvenTreeAPI class"""

        # Each of these URLs should be invalid
        for url in [
            "test.com/123",
            "http://:80/123",
            "//xyz.co.uk",
        ]:
            with self.assertRaises(Exception):
                a = api.InvenTreeAPI(url, connect=False)

        # test for base URL construction
        a = api.InvenTreeAPI('https://test.com', connect=False)
        self.assertEqual(a.base_url, 'https://test.com/')
        self.assertEqual(a.api_url, 'https://test.com/api/')

        # more tests that the base URL is set correctly under specific conditions
        urls = [
            "http://a.b.co:80/sub/dir/api/",
            "http://a.b.co:80/sub/dir/api",
            "http://a.b.co:80/sub/dir/",
            "http://a.b.co:80/sub/dir",
        ]

        for url in urls:
            a = api.InvenTreeAPI(url, connect=False)
            self.assertEqual(a.base_url, "http://a.b.co:80/sub/dir/")
            self.assertEqual(a.api_url, "http://a.b.co:80/sub/dir/api/")

    def test_url_construction(self):
        """Test that the API class correctly constructs URLs"""

        a = api.InvenTreeAPI("http://localhost:1234", connect=False)

        tests = {
            'part': 'http://localhost:1234/api/part/',
            '/part': 'http://localhost:1234/api/part/',
            '/part/': 'http://localhost:1234/api/part/',
            'order/so/shipment': 'http://localhost:1234/api/order/so/shipment/',
        }

        for endpoint, url in tests.items():
            self.assertEqual(a.constructApiUrl(endpoint), url)


class LoginTests(unittest.TestCase):

    def test_failed_logins(self):

        # Attempt connection where no server exists
        with self.assertRaises(Exception):
            a = api.InvenTreeAPI("http://127.0.0.1:9999", username="admin", password="password")

        # Attempt connection with invalid credentials
        with self.assertRaises(Exception):
            a = api.InvenTreeAPI(SERVER, username="abcde", password="********")

            self.assertIsNotNone(a.server_details)
            self.assertIsNone(a.token)


class Unauthenticated(unittest.TestCase):
    """
    Test that we cannot access the data if we are not authenticated.
    """

    def setUp(self):
        self.api = api.InvenTreeAPI(SERVER, username="hello", password="world", connect=False)

    def test_read_parts(self):

        with self.assertRaises(Exception) as ar:
            part.Part.list(self.api)

        self.assertIn('Authentication at InvenTree server failed', str(ar.exception))

    def test_file_download(self):
        """
        Attempting to download a file while unauthenticated should raise an error
        """

        # Downloading without auth = unauthorized error (401)
        with self.assertRaises(requests.exceptions.HTTPError):
            self.assertFalse(self.api.downloadFile('/media/part/files/1/test.pdf', 'test.pdf'))


class Timeout(unittest.TestCase):
    """
    Test that short timeout leads to correct error
    """

    def test_timeout(self):
        """
        This unrealistically short timeout should lead to a timeout error
        """
        # Attempt connection with short timeout
        with self.assertRaises(requests.exceptions.ReadTimeout):
            a = api.InvenTreeAPI(SERVER, username=USERNAME, password=PASSWORD, timeout=0.001)  # noqa: F841


class InvenTreeTestCase(unittest.TestCase):
    """
    Base class for running InvenTree unit tests.

    - Creates an authenticated API instance
    """

    def setUp(self):
        """
        Test case setup functions
        """
        self.api = api.InvenTreeAPI(
            SERVER,
            username=USERNAME, password=PASSWORD,
            timeout=30,
            token_name='python-test',
            use_token_auth=True
        )


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

        with self.assertRaises(requests.exceptions.ReadTimeout):
            # Test short timeout for a specific function
            c = part.PartCategory.create(self.api, {
                'parent': None,
                'name': 'My custom category',
                'description': 'A part category',
            }, timeout=0.001)

        n = part.PartCategory.count(self.api)

        # Create a custom category
        c = part.PartCategory.create(self.api, {
            'parent': None,
            'name': f'Custom category {n + 1}',
            'description': 'A part category',
        })

        self.assertIsNotNone(c)
        self.assertIsNotNone(c.pk)

        n = part.Part.count(self.api)

        p = part.Part.create(self.api, {
            'name': f'ACME Widget {n}',
            'description': 'A simple widget created via the API',
            'category': c.pk,
            'ipn': f'ACME-0001-{n}',
            'virtual': False,
            'active': True
        })

        self.assertIsNotNone(p)
        self.assertEqual(p.category, c.pk)

        cat = p.getCategory()
        self.assertEqual(cat.pk, c.pk)

        s = stock.StockItem.create(self.api, {
            'part': p.pk,
            'quantity': 45,
            'notes': 'This is a note',

        })

        self.assertIsNotNone(s)
        self.assertEqual(s.part, p.pk)

        prt = s.getPart()
        self.assertEqual(prt.pk, p.pk)
        self.assertEqual(prt.name, f'ACME Widget {n}')


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
