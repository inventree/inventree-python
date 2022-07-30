"""
Unit test for basic model class functionality
"""

import os
import sys

sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from inventree.base import InventreeObject  # noqa: E402
from test_api import InvenTreeTestCase

class BaseModelTests(InvenTreeTestCase):
    """Simple unit tests for the InvenTreeObject class"""
    
    def test_create(self):
        """Unit tests for InventreeObject creation"""

        with self.assertRaises(TypeError):
            InventreeObject(None, pk='test')
    
        for pk in [-1, 0]:
            with self.assertRaises(ValueError):
                InventreeObject(None, pk=pk)