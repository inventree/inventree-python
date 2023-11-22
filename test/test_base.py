"""
Unit test for basic model class functionality
"""

import os
import sys

sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from test_api import InvenTreeTestCase  # noqa: E402

from inventree.base import InventreeObject  # noqa: E402


class BaseModelTests(InvenTreeTestCase):
    """Simple unit tests for the InvenTreeObject class"""

    def test_create(self):
        """Unit tests for InventreeObject creation"""

        # Test with non-int pk
        with self.assertRaises(TypeError):
            InventreeObject(None, pk='test')

        # Test with invalid pk
        for pk in [-1, 0]:
            with self.assertRaises(ValueError):
                InventreeObject(None, pk=pk)

        # Test with pk supplied in data
        with self.assertRaises(TypeError):
            InventreeObject(
                None,
                data={
                    'pk': 'seven',
                }
            )

    def test_data_access(self):
        """Test data access functionality"""

        obj = InventreeObject(
            None,
            data={
                "pk": "10",
                "hello": "world",
                "name": "My name",
                "description": "My description",
            }
        )

        # Test __getattr__ access
        self.assertEqual(obj.pk, 10)
        self.assertEqual(obj.name, "My name")

        with self.assertRaises(AttributeError):
            print(obj.doesNotExist)

        # Test __getitem__ access
        self.assertEqual(obj['description'], 'My description')
        self.assertEqual(obj['pk'], '10')
        self.assertEqual(obj['hello'], 'world')

        for k in ['fake', 'data', 'values']:
            with self.assertRaises(KeyError):
                print(obj[k])
