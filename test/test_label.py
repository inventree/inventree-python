# -*- coding: utf-8 -*-

import os
import sys

sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from test_api import InvenTreeTestCase  # noqa: E402

from inventree.label import LabelTemplate  # noqa: E402
from inventree.part import Part  # noqa: E402
from inventree.plugin import InvenTreePlugin  # noqa: E402


class LabelTemplateTests(InvenTreeTestCase):
    """Unit tests for label templates and printing, using the modern API."""

    def test_label_template_list(self):
        """List available label templates."""

        n = LabelTemplate.count(self.api)
        templates = LabelTemplate.list(self.api)

        self.assertEqual(n, len(templates))
        self.assertGreater(len(templates), 0)

        # Check some expected attributes
        for attr in ['name', 'description', 'enabled', 'model_type', 'template']:
            for template in templates:
                self.assertIn(attr, template)

        for idx, template in enumerate(templates):
            enabled = idx > 0

            if template.enabled != enabled:
                template.save(data={'enabled': idx > 0})

        # Filter by 'enabled' status
        templates = LabelTemplate.list(self.api, enabled=True)
        self.assertGreater(len(templates), 0)
        self.assertLess(len(templates), n)

        # Filter by 'disabled' status
        templates = LabelTemplate.list(self.api, enabled=False)
        self.assertGreater(len(templates), 0)
        self.assertLess(len(templates), n)

    def test_label_print(self):
        """Print a template!"""

        # Find a part to print
        part = Part.list(self.api, limit=1)[0]

        templates = part.getLabelTemplates()
        self.assertGreater(len(templates), 0)

        template = templates[0]

        # Find an available plugin
        plugins = InvenTreePlugin.list(self.api, active=True, mixin='labels')
        self.assertGreater(len(plugins), 0)

        plugin = plugins[0]

        response = part.printLabel(template, plugin=plugin)

        for key in ['created', 'model_type', 'complete', 'output', 'template', 'plugin']:
            self.assertIn(key, response)
        
        self.assertEqual(response['complete'], True)
        self.assertEqual(response['model_type'], 'part')
        self.assertIsNotNone(response['output'])
        self.assertEqual(response['template'], template.pk)
        self.assertEqual(response['plugin'], plugin.key)
