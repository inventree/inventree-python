# -*- coding: utf-8 -*-

import os
import sys

try:
    import Image
except ImportError:
    from PIL import Image

sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from test_api import InvenTreeTestCase  # noqa: E402

from inventree import part  # noqa: E402


class PartTest(InvenTreeTestCase):
    """
    Test for PartCategory and Part objects.
    """

    def test_fields(self):
        """
        Test field names via OPTIONS request
        """

        field_names = part.Part.fieldNames(self.api)

        self.assertIn('active', field_names)
        self.assertIn('revision', field_names)
        self.assertIn('full_name', field_names)
        self.assertIn('IPN', field_names)

    def test_part_cats(self):
        """
        Tests for category filtering
        """

        # All categories
        cats = part.PartCategory.list(self.api)
        n = len(cats)
        self.assertTrue(len(cats) >= 9)

        # Filtered categories must be fewer than *all* categories
        cats = part.PartCategory.list(self.api, parent=1)

        self.assertGreater(len(cats), 0)
        self.assertLess(len(cats), n)

    def test_elec(self):
        electronics = part.PartCategory(self.api, 1)

        # This is a top-level category, should not have a parent!
        self.assertIsNone(electronics.getParentCategory())
        self.assertEqual(electronics.name, "Electronics")

        children = electronics.getChildCategories()
        self.assertEqual(len(children), 1)
        
        passives = children[0]
        self.assertEqual(passives.name, 'Passives')
        
        # Grab all child categories
        children = part.PartCategory.list(self.api, parent=passives.pk)
        self.assertEqual(len(children), 3)

        children = passives.getChildCategories()
        self.assertEqual(len(children), 3)
        
        parent = passives.getParentCategory()
        self.assertEqual(parent.pk, 1)
        self.assertEqual(parent.name, 'Electronics')
        
    def test_caps(self):

        # Capacitors
        capacitors = part.PartCategory(self.api, 6)
        self.assertEqual(capacitors.name, "Capacitors")
        parts = capacitors.getParts()
        self.assertEqual(len(parts), 4)

        for p in parts:
            self.assertEqual(p.category, capacitors.pk)

    def test_part_list(self):
        """
        Check that we can list Part objects,
        and apply certain filters
        """

        parts = part.Part.list(self.api)
        self.assertTrue(len(parts) >= 19)

        parts = part.Part.list(self.api, category=5)
        self.assertTrue(len(parts) >= 3)

    def test_part_edit(self):
        """
        Test that we can edit a part
        """

        # Select a part
        p = part.Part.list(self.api)[-1]

        name = p.name

        # Ajdust the name
        if len(name) < 40:
            name += '_append'
        else:
            name = name[:-10]

        p.save(
            data={
                'name': name,
                'description': 'A new description'
            },
        )
        p.reload()

        self.assertEqual(p.name, name)
        self.assertEqual(p.description, 'A new description')

    def test_default_values(self):
        """
        Test that the DRF framework will correctly insert the default values
        """

        n = len(part.Part.list(self.api))

        # Create a part without specifying 'active' and 'virtual' fields
        p = part.Part.create(
            self.api,
            {
                'name': f"Part_{n}_default_test",
                'category': 1,
                'description': "Some part thingy",
            }
        )

        self.assertEqual(p.active, True)
        self.assertEqual(p.virtual, False)

        # Set both to false
        p = part.Part.create(
            self.api,
            {
                'name': f"Part_{n}_default_test_2",
                'category': 1,
                'description': 'Setting fields to false',
                'active': False,
                'virtual': False,
            }
        )

        self.assertFalse(p.active)
        self.assertFalse(p.virtual)

        # Set both to true
        p = part.Part.create(
            self.api,
            {
                'name': f"Part_{n}_default_test_3",
                'category': 1,
                'description': 'Setting fields to true',
                'active': True,
                'virtual': True,
            }
        )

        self.assertTrue(p.active)
        self.assertTrue(p.virtual)

    def test_part_delete(self):
        """
        Test we can create and delete a Part instance via the API
        """
        
        n = len(part.Part.list(self.api))

        # Create a new part
        # We do not specify 'active' value so it will default to True
        p = part.Part.create(
            self.api,
            {
                'name': 'Delete Me',
                'description': 'Not long for this world!',
                'category': 1,
            }
        )

        self.assertIsNotNone(p)
        self.assertIsNotNone(p.pk)

        self.assertEqual(len(part.Part.list(self.api)), n + 1)

        # Cannot delete - part is 'active'!
        response = p.delete()
        self.assertEqual(response.status_code, 405)

        p.save(data={'active': False})
        response = p.delete()
        self.assertEqual(response.status_code, 204)

        # And check that the part has indeed been deleted
        self.assertEqual(len(part.Part.list(self.api)), n)

    def test_image_upload(self):
        """
        Test image upload functionality for Part model
        """

        # Grab the first part
        p = part.Part.list(self.api)[0]

        # Ensure the part does *not* have an image associated with it
        p.save(data={'image': None})

        # Create a dummy file (not an image)
        with open('dummy_image.jpg', 'w') as dummy_file:
            dummy_file.write("hello world")

        # Attempt to upload an image
        response = p.uploadImage("dummy_image.jpg")
        self.assertIsNone(response)

        # Now, let's actually upload a real image
        img = Image.new('RGB', (128, 128), color='red')
        img.save('dummy_image.png')

        response = p.uploadImage("dummy_image.png")

        self.assertIsNotNone(response)
        self.assertIsNotNone(p['image'])
        self.assertIn('dummy_image', p['image'])

        # TODO: Re-download the image
