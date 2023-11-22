# -*- coding: utf-8 -*-

"""
Unit test for the Build models
"""

import os
import sys

sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from test_api import InvenTreeTestCase  # noqa: E402

from inventree.build import Build, BuildAttachment  # noqa: E402


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

        build = self.get_build()

        n = len(BuildAttachment.list(self.api, build=build.pk))

        # Upload *this* file
        fn = os.path.join(os.path.dirname(__file__), 'test_build.py')

        response = build.uploadAttachment(fn, comment='A self referencing upload!')

        self.assertEqual(response['build'], build.pk)
        self.assertEqual(response['comment'], 'A self referencing upload!')

        self.assertEqual(len(build.getAttachments()), n + 1)

    def test_build_attachment_bulk_delete(self):
        """Test 'bulk delete' operation for the BuildAttachment class"""

        build = self.get_build()

        n = len(BuildAttachment.list(self.api, build=build.pk))

        fn = os.path.join(os.path.dirname(__file__), 'test_build.py')

        pk_values = []

        # Create a number of new attachments
        for i in range(10):
            response = build.uploadAttachment(fn, comment=f"Build attachment {i}")
            pk_values.append(response['pk'])

        self.assertEqual(len(BuildAttachment.list(self.api, build=build.pk)), n + 10)

        # Call without providing required arguments
        with self.assertRaises(ValueError):
            BuildAttachment.bulkDelete(self.api)

        BuildAttachment.bulkDelete(self.api, items=pk_values)

        # The number of attachments has been reduced to the original value
        self.assertEqual(len(BuildAttachment.list(self.api, build=build.pk)), n)

        # Now, delete using the 'filters' argument
        for i in range(99, 109):
            response = build.uploadAttachment(fn, comment=f"Build attachment {i}")
            pk_values.append(response['pk'])

        self.assertEqual(len(BuildAttachment.list(self.api, build=build.pk)), n + 10)

        response = BuildAttachment.bulkDelete(
            self.api,
            filters={
                "build": build.pk,
            }
        )

        # All attachments for this Build should have been deleted
        self.assertEqual(len(BuildAttachment.list(self.api, build=build.pk)), 0)

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

        # Complete the build, even though it is not completed
        build.complete(accept_unallocated=True, accept_incomplete=True)

        # Check status
        self.assertEqual(build.status, 40)
        self.assertEqual(build.status_text, 'Complete')
