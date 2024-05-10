# -*- coding: utf-8 -*-

import os
import sys

sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from test_api import InvenTreeTestCase  # noqa: E402

from inventree.plugin import InvenTreePlugin

class PluginTest(InvenTreeTestCase):
    """Unit tests for plugin functionality."""

    def test_plugin_list(self):
        """Test plugin list API."""

        plugins = InvenTreePlugin.list(self.api)

        for plugin in plugins:
            print(plugin._data)

