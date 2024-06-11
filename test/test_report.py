# -*- coding: utf-8 -*-

import os
import sys

sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from test_api import InvenTreeTestCase  # noqa: E402

from inventree.build import Build  # noqa: E402
from inventree.report import ReportTemplate  # noqa: E402


class ReportClassesTest(InvenTreeTestCase):
    """Tests for Report functions models"""

    def test_list_templates(self):
        """List the available report templates."""

        templates = ReportTemplate.list(self.api)

        self.assertGreater(len(templates), 0)

        for template in templates:
            for key in ['name', 'description', 'enabled', 'model_type', 'template']:
                self.assertIn(key, template)

        # disable a template
        templates[0].save(data={'enabled': False})

        templates = ReportTemplate.list(self.api, enabled=False)
        self.assertGreater(len(templates), 0)

        # enable a template
        templates[0].save(data={'enabled': True})

        templates = ReportTemplate.list(self.api, enabled=True)
        self.assertGreater(len(templates), 0)
    
    def test_print_report(self):
        """Test report printing."""

        # Find a build to print
        build = Build.list(self.api, limit=1)[0]

        templates = build.getReportTemplates()
        self.assertGreater(len(templates), 0)

        template = templates[0]

        # Print the report
        response = build.printReport(template)

        for key in ['pk', 'model_type', 'output', 'template']:
            self.assertIn(key, response)
        
        self.assertIsNotNone(response['output'])
        self.assertEqual(response['template'], template.pk)
        self.assertEqual(response['model_type'], build.getModelType())
