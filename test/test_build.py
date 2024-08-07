# -*- coding: utf-8 -*-

"""
Unit test for the Build models
"""

import os
import sys

sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from test_api import InvenTreeTestCase  # noqa: E402

from inventree.base import Attachment  # noqa: E402
from inventree.build import Build  # noqa: E402


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
                    "title": "Automated test build",
                    "part": 25,
                    "quantity": 100,
                    "reference": f"BO-{n+1:04d}",
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

        if self.api.api_version < Attachment.MIN_API_VERSION:
            return

        build = self.get_build()

        n = len(build.getAttachments())

        # Upload *this* file
        fn = os.path.join(os.path.dirname(__file__), 'test_build.py')

        response = build.uploadAttachment(fn, comment='A self referencing upload!')

        self.assertEqual(response['model_type'], 'build')
        self.assertEqual(response['model_id'], build.pk)
        self.assertEqual(response['comment'], 'A self referencing upload!')

        self.assertEqual(len(build.getAttachments()), n + 1)

    def test_build_cancel(self):
        """
        Test cancelling a build order.
        """

        n = len(Build.list(self.api))

        # Create a new build order
        build = Build.create(
            self.api,
            {
                "title": "Automated test build",
                "part": 25,
                "quantity": 100,
                "reference": f"BO-{n+1:04d}"
            }
        )

        # Cancel
        build.cancel()

        # Check status
        self.assertEqual(build.status, 30)
        self.assertEqual(build.status_text, 'Cancelled')

    def test_build_complete(self):
        """
        Test completing a build order.
        """

        n = len(Build.list(self.api))

        # Create a new build order
        build = Build.create(
            self.api,
            {
                "title": "Automated test build",
                "part": 25,
                "quantity": 100,
                "reference": f"BO-{n+1:04d}"
            }
        )

        # Check that build status is pending
        self.assertEqual(build.status, 10)

        if self.api.api_version >= 233:
            # Issue the build order
            build.issue()
            self.assertEqual(build.status, 20)

            # Mark build order as "on hold" again
            build.hold()
            self.assertEqual(build.status, 25)

            # Issue again
            build.issue()
            self.assertEqual(build.status, 20)

        # Complete the build, even though it is not completed
        build.complete(accept_unallocated=True, accept_incomplete=True)

        # Check status
        self.assertEqual(build.status, 40)
        self.assertEqual(build.status_text, 'Complete')
