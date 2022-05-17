# -*- coding: utf-8 -*-

import os
import requests
import sys

try:
    import Image
except ImportError:
    from PIL import Image

sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from test_api import InvenTreeTestCase  # noqa: E402

from inventree.part import Part, PartAttachment, PartCategory  # noqa: E402
from inventree.part import InternalPrice  # noqa: E402


class PartTest(InvenTreeTestCase):
    """
    Test for PartCategory and Part objects.
    """

    def test_access_erors(self):
        """
        Test that errors are flagged when we try to access an invalid part
        """

        with self.assertRaises(TypeError):
            Part(self.api, 'hello')
        
        with self.assertRaises(ValueError):
            Part(self.api, -1)

        # Try to access a Part which does not exist
        with self.assertRaises(requests.exceptions.HTTPError):
            Part(self.api, 9999999999999)

    def test_fields(self):
        """
        Test field names via OPTIONS request
        """

        field_names = Part.fieldNames(self.api)

        self.assertIn('active', field_names)
        self.assertIn('revision', field_names)
        self.assertIn('full_name', field_names)
        self.assertIn('IPN', field_names)

    def test_part_cats(self):
        """
        Tests for category filtering
        """

        # All categories
        cats = PartCategory.list(self.api)
        n = len(cats)
        self.assertTrue(len(cats) >= 9)

        # Filtered categories must be fewer than *all* categories
        cats = PartCategory.list(self.api, parent=1)

        self.assertGreater(len(cats), 0)
        self.assertLess(len(cats), n)

    def test_elec(self):
        electronics = PartCategory(self.api, 1)

        # This is a top-level category, should not have a parent!
        self.assertIsNone(electronics.getParentCategory())
        self.assertEqual(electronics.name, "Electronics")

        children = electronics.getChildCategories()
        self.assertGreaterEqual(len(children), 3)

        for child in children:
            self.assertEqual(child.parent, 1)
        
        child = PartCategory(self.api, pk=3)
        self.assertEqual(child.name, 'Capacitors')
        self.assertEqual(child.getParentCategory().pk, electronics.pk)
        
        # Grab all child categories
        children = PartCategory.list(self.api, parent=child.pk)

        n = len(children)

        for c in children:
            self.assertEqual(c.parent, child.pk)

        # Create some new categories under this one
        for idx in range(3):
            name = f"Subcategory {n+idx}"

            cat = PartCategory.create(self.api, {
                "parent": child.pk,
                "name": name,
                "description": "A new subcategory",
            })

            self.assertEqual(cat.parent, child.pk)
            self.assertEqual(cat.name, name)

            # Edit the name of the new location
            cat.save({
                "name": f"{name}_suffix",
            })

            # Reload from server, and check
            cat.reload()
            self.assertEqual(cat.name, f"{name}_suffix")

        # Number of children should have increased!
        self.assertEqual(len(child.getChildCategories()), n + 3)
        
    def test_caps(self):

        cat = PartCategory(self.api, 6)
        self.assertEqual(cat.name, "Transceivers")
        parts = cat.getParts()

        n_parts = len(parts)

        for p in parts:
            self.assertEqual(p.category, cat.pk)

        # Create some new parts
        for i in range(10):

            name = f"Part_{cat.pk}_{n_parts + i}"

            prt = Part.create(self.api, {
                "category": cat.pk,
                "name": name,
                "description": "A new part in this category",
            })

            self.assertIsNotNone(prt)

            self.assertEqual(prt.name, name)
        
        parts = cat.getParts()

        self.assertEqual(len(parts), n_parts + 10)

    def test_part_list(self):
        """
        Check that we can list Part objects,
        and apply certain filters
        """

        parts = Part.list(self.api)
        self.assertTrue(len(parts) >= 19)

        parts = Part.list(self.api, category=5)

        n = len(parts)

        for i in range(5):
            prt = Part.create(self.api, {
                "category": 5,
                "name": f"Special Part {n+i}",
                "description": "A new part in this category!",
            })

            self.assertEqual(prt.category, 5)
            cat = prt.getCategory()
            self.assertEqual(cat.pk, 5)

            parts = cat.getParts()

            self.assertGreaterEqual(len(parts), i + 1)

    def test_part_edit(self):
        """
        Test that we can edit a part
        """

        # Select a part
        p = Part.list(self.api)[-1]

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

        n = len(Part.list(self.api))

        # Create a part without specifying 'active' and 'virtual' fields
        p = Part.create(
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
        p = Part.create(
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
        p = Part.create(
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
        
        n = len(Part.list(self.api))

        # Create a new part
        # We do not specify 'active' value so it will default to True
        p = Part.create(
            self.api,
            {
                'name': 'Delete Me',
                'description': 'Not long for this world!',
                'category': 1,
            }
        )

        self.assertIsNotNone(p)
        self.assertIsNotNone(p.pk)

        self.assertEqual(len(Part.list(self.api)), n + 1)

        # Cannot delete - part is 'active'!
        with self.assertRaises(requests.exceptions.HTTPError) as ar:
            response = p.delete()

        self.assertIn("is active: cannot delete", str(ar.exception))

        p.save(data={'active': False})
        response = p.delete()
        self.assertEqual(response.status_code, 204)

        # And check that the part has indeed been deleted
        self.assertEqual(len(Part.list(self.api)), n)

    def test_image_upload(self):
        """
        Test image upload functionality for Part model
        """

        # Grab the first part
        p = Part.list(self.api)[0]

        # Ensure the part does *not* have an image associated with it
        p.save(data={'image': None})

        # Create a dummy file (not an image)
        with open('dummy_image.jpg', 'w') as dummy_file:
            dummy_file.write("hello world")

        # Attempt to upload an image
        with self.assertRaises(requests.exceptions.HTTPError):
            response = p.uploadImage("dummy_image.jpg")
    
        # Now, let's actually upload a real image
        img = Image.new('RGB', (128, 128), color='red')
        img.save('dummy_image.png')

        response = p.uploadImage("dummy_image.png")

        self.assertIsNotNone(response)
        self.assertIsNotNone(p['image'])
        self.assertIn('dummy_image', p['image'])

        # Re-download the image file
        fout = 'test/output.png'

        if os.path.exists(fout):
            # Delete the file if it already exists
            os.remove(fout)

        response = p.downloadImage(fout)
        self.assertTrue(response)

        self.assertTrue(os.path.exists(fout))

        # Attempt to re-download
        with self.assertRaises(FileExistsError):
            p.downloadImage(fout)

        # Download, with overwrite enabled
        p.downloadImage(fout, overwrite=True)

    def test_part_attachment(self):
        """
        Check that we can upload attachment files against the part
        """

        prt = Part(self.api, pk=1)
        attachments = PartAttachment.list(self.api, part=1)

        for a in attachments:
            self.assertEqual(a.part, 1)

        n = len(attachments)

        # Test that a file upload without the required 'part' parameter fails
        with self.assertRaises(ValueError):
            PartAttachment.upload(self.api, 'test-file.txt')

        # Test that attempting to upload an invalid file fails
        with self.assertRaises(FileNotFoundError):
            PartAttachment.upload(self.api, 'test-file.txt', part=1)

        # Check that no new files have been uploaded
        self.assertEqual(len(PartAttachment.list(self.api, part=1)), n)

        # Test that we can upload a file by filename, directly from the Part instance
        filename = os.path.join(os.path.dirname(__file__), 'docker-compose.yml')

        response = prt.uploadAttachment(
            filename,
            comment='Uploading a file'
        )

        self.assertIsNotNone(response)
        
        pk = response['pk']

        # Check that a new attachment has been created!
        attachment = PartAttachment(self.api, pk=pk)
        self.assertTrue(attachment.is_valid())

        # Download the attachment to a local file!
        dst = os.path.join(os.path.dirname(__file__), 'test.tmp')
        attachment.download(dst, overwrite=True)

        self.assertTrue(os.path.exists(dst))
        self.assertTrue(os.path.isfile(dst))

        with self.assertRaises(FileExistsError):
            # Attempt to download the file again, but without overwrite option
            attachment.download(dst)

    def test_set_price(self):
        """
        Tests that an internal price can be set for a part
        """

        test_price = 100.0
        test_quantity = 1

        # Grab the first part
        p = Part.list(self.api)[0]

        # Grab all internal prices for the part
        ip = InternalPrice.list(self.api, part=p.pk)

        # Delete any existsing prices
        for price in ip:
            self.assertEqual(type(price), InternalPrice)
            price.delete()

        # Ensure that no part has an internal price
        ip = InternalPrice.list(self.api, part=p.pk)
        self.assertEqual(len(ip), 0)

        # Set the internal price
        p.setInternalPrice(test_quantity, test_price)

        # Ensure that the part has an internal price
        ip = InternalPrice.list(self.api, part=p.pk)
        self.assertEqual(len(ip), 1)
        
        # Grab the internal price
        ip = ip[0]

        self.assertEqual(ip.quantity, test_quantity)
        self.assertEqual(ip.part, p.pk)
        ip_price_clean = float(ip.price)
        self.assertEqual(ip_price_clean, test_price)
