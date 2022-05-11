# -*- coding: utf-8 -*-

"""
Unit test for the Build models
"""

import os
import sys

sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from inventree.build import Build, BuildAttachment  # noqa: E402

from test_api import InvenTreeTestCase  # noqa: E402


class BuildOrderTest(InvenTreeTestCase):
    """
    Unit tests for Build model
    """

    def get_build(self):
        """
        Return a BuildOrder from the database
        If a build does not already exist, create a new one
        """

        builds = Build.list(self.api)

        n = len(builds)

        if n == 0:
            # Create a new build order
            build = Build.create(
                self.api,
                {
                    "part": 25,
                    "quantity": 100,
                    "reference": f"{n+1}"
                }
            )
        else:
            build = builds[-1]
        
        return build

    def test_list_builds(self):
        
        build = self.get_build()
        
        self.assertIsNotNone(build)

        builds = Build.list(self.api)

        self.assertGreater(len(builds), 0)
    
    def test_build_attachment(self):
        """
        Test that we can upload an attachment against a Build
        """

        build = self.get_build()

        n = len(BuildAttachment.list(self.api, build=build.pk))

        # Upload *this* file
        fn = os.path.join(os.path.dirname(__file__), 'test_build.py')

        response = build.uploadAttachment(fn, comment='A self referencing upload!')

        self.assertEqual(response['build'], build.pk)
        self.assertEqual(response['comment'], 'A self referencing upload!')

        self.assertEqual(len(build.getAttachments()), n + 1)
