"""Unit tests for the ProjectCode model"""

import sys
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from inventree.project_code import ProjectCode
from test_api import InvenTreeTestCase  # noqa: E402


class ProjectCodeTest(InvenTreeTestCase):
    """Tests for the ProjectCode model"""

    def test_project_code_create(self):
        """Test we can create a new project code"""
            
        n = ProjectCode.count(self.api)

        ProjectCode.create(self.api, {
            'code': 'TEST',
            'description': 'Test project code',
        })

        self.assertEqual(ProjectCode.count(self.api), n + 1)

        # Try to create a duplicate code
        with self.assertRaises(Exception):
            ProjectCode.create(self.api, {
                'code': 'TEST',
                'description': 'Test project code',
            })

        # Create 5 more codes
        for idx in range(5):
            ProjectCode.create(self.api, {
                'code': f'CODE-{idx}',
                'description': f'Description {idx}',
            })
        
        # List all codes
        codes = ProjectCode.list(self.api)

        self.assertEqual(len(codes), n + 6)
