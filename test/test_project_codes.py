"""Unit tests for the ProjectCode model"""

import os
import sys

sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from test_api import InvenTreeTestCase  # noqa: E402

from inventree.project_code import ProjectCode  # noqa: E402


class ProjectCodeTest(InvenTreeTestCase):
    """Tests for the ProjectCode model"""

    def test_project_code_create(self):
        """Test we can create a new project code"""

        n = ProjectCode.count(self.api)

        ProjectCode.create(self.api, {
            'code': f'TEST {n + 1}',
            'description': 'Test project code',
        })

        self.assertEqual(ProjectCode.count(self.api), n + 1)

        # Try to create a duplicate code
        with self.assertRaises(Exception):
            ProjectCode.create(self.api, {
                'code': f'TEST {n + 1}',
                'description': 'Test project code',
            })

        n = ProjectCode.count(self.api)

        # Create 5 more codes
        for idx in range(5):
            ProjectCode.create(self.api, {
                'code': f'CODE-{idx + n}',
                'description': f'Description {idx + n}',
            })

        # List all codes
        codes = ProjectCode.list(self.api)

        self.assertEqual(len(codes), n + 5)
