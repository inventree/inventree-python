# -*- coding: utf-8 -*-

import os
import sys

sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from test_api import InvenTreeTestCase  # noqa: E402

from inventree.plugin import InvenTreePlugin  # noqa: E402


class PluginTest(InvenTreeTestCase):
    """Unit tests for plugin functionality."""

    def test_plugin_lookup(self):
        """Test plugin lookup by key."""

        if self.api.api_version < InvenTreePlugin.MIN_API_VERSION:
            return

        plugins = InvenTreePlugin.list(self.api)

        self.assertGreater(len(plugins), 0)

        p1 = plugins[0]

        # Access the plugin via primary key value
        p2 = InvenTreePlugin(self.api, p1.key)

        self.assertEqual(p1.key, p2.key)
        self.assertEqual(p1.name, p2.name)

        self.assertEqual(p1._data['pk'], p2._data['pk'])

    def test_plugin_list(self):
        """Test plugin list API."""

        if self.api.api_version < InvenTreePlugin.MIN_API_VERSION:
            return

        plugins = InvenTreePlugin.list(self.api)

        expected_attributes = [
            'pk',
            'key',
            'name',
            'package_name',
            'active',
            'meta',
            'mixins',
            'is_builtin',
            'is_sample',
            'is_installed'
        ]

        for plugin in plugins:
            for key in expected_attributes:
                self.assertIn(key, plugin)

    def test_filter_by_active(self):
        """Filter by plugin active status."""

        if self.api.api_version < InvenTreePlugin.MIN_API_VERSION:
            return

        plugins = InvenTreePlugin.list(self.api, active=True)
        self.assertGreater(len(plugins), 0)

        plugin = plugins[0]

        for plugin in plugins:
            self.assertTrue(plugin.active)

    def test_filter_by_builtin(self):
        """Filter by plugin builtin status."""

        if self.api.api_version < InvenTreePlugin.MIN_API_VERSION:
            return

        plugins = InvenTreePlugin.list(self.api, builtin=True)
        self.assertGreater(len(plugins), 0)

        for plugin in plugins:
            self.assertTrue(plugin.is_builtin)
    
    def test_filter_by_mixin(self):
        """Test that we can filter by 'mixin' attribute."""

        if self.api.api_version < InvenTreePlugin.MIN_API_VERSION:
            return

        n = InvenTreePlugin.count(self.api)

        plugins = InvenTreePlugin.list(self.api, mixin='labels')

        self.assertLess(len(plugins), n)
        self.assertGreater(len(plugins), 0)

        for plugin in plugins:
            self.assertIn('labels', plugin.mixins)
