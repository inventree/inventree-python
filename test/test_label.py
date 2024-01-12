# -*- coding: utf-8 -*-

import os
import sys

sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from test_api import InvenTreeTestCase  # noqa: E402

from inventree.label import LabelLocation, LabelPart, LabelStock  # noqa: E402
from inventree.part import Part  # noqa: E402
from inventree.stock import StockItem, StockLocation  # noqa: E402


class LabelTest(InvenTreeTestCase):
    """Tests for Label functions models"""

    def test_label_list(self):
        """
        Test for using listing functionality of each type of label
        """

        # Parts
        # Get label list
        lbl_part_list = LabelPart.list(self.api)

        # Make a new list filtered by LabelPart
        # List should be non-zero length
        # Filtered list should be equal the original list
        lbl_part_list_filtered = [x for x in lbl_part_list if isinstance(x, LabelPart)]

        self.assertGreater(len(lbl_part_list_filtered), 0)
        self.assertEqual(lbl_part_list, lbl_part_list_filtered)

        # Stock Items
        # Get label list
        lbl_stock_list = LabelStock.list(self.api)

        # Make a new list filtered by LabelPart
        # List should be non-zero length
        # Filtered list should be equal the original list
        lbl_stock_list_filtered = [x for x in lbl_stock_list if isinstance(x, LabelStock)]

        self.assertGreater(len(lbl_stock_list_filtered), 0)
        self.assertEqual(lbl_stock_list, lbl_stock_list_filtered)

        # Stock Locations
        # Get label list
        lbl_location_list = LabelLocation.list(self.api)

        # Make a new list filtered by LabelPart
        # List should be non-zero length
        # Filtered list should be equal the original list
        lbl_location_list_filtered = [x for x in lbl_location_list if isinstance(x, LabelLocation)]

        self.assertGreater(len(lbl_location_list_filtered), 0)
        self.assertEqual(lbl_location_list, lbl_location_list_filtered)

    def test_label_create_download(self):
        """
        Tests creating a new label from API, by uploading the dummy template file
        """

        def comparefiles(file1, file2):
            """Compare content of two files, return True if equal, else False"""

            F1 = open(file1, 'r')
            contents_1 = F1.read()
            F1.close()

            F2 = open(file2, 'r')
            contents_2 = F2.read()
            F2.close()

            return contents_1 == contents_2

        dummytemplate = os.path.join(os.path.dirname(__file__), 'dummytemplate.html')
        dummytemplate2 = os.path.join(os.path.dirname(__file__), 'dummytemplate2.html')

        for RepClass in (LabelPart, LabelStock, LabelLocation):
            # Test for all Label classes sequentially

            #
            # Test with file name
            #

            # Create a new label based on the dummy template
            newlabel = RepClass.create(
                self.api,
                {'name': 'Dummy label', 'description': 'Label created as test'},
                dummytemplate
            )

            # The return value should be a LabelPart object
            self.assertIsInstance(newlabel, RepClass)

            # Try to download the template file
            newlabel.downloadTemplate(destination="dummytemplate_download.html")

            self.assertTrue(comparefiles("dummytemplate_download.html", dummytemplate))

            # Remove the test file
            os.remove("dummytemplate_download.html")

            #
            # Test with open(...)
            #

            # Create a new label based on the dummy template
            with open(dummytemplate) as template_upload:
                newlabel2 = RepClass.create(
                    self.api,
                    {'name': 'Dummy label', 'description': 'Label created as test'},
                    template_upload
                )

            # The return value should be a LabelPart object
            self.assertIsInstance(newlabel2, RepClass)

            # Try to download the template file
            newlabel2.downloadTemplate(destination="dummytemplate_download.html")

            self.assertTrue(comparefiles("dummytemplate_download.html", dummytemplate))

            # Remove the test file
            os.remove("dummytemplate_download.html")

            #
            # Test overwriting the label file with save method
            # Use file name
            #

            newlabel2.save(data=None, label=dummytemplate2)

            # Try to download the template file
            newlabel2.downloadTemplate(destination="dummytemplate2_download.html")

            self.assertTrue(comparefiles("dummytemplate2_download.html", dummytemplate2))
            # Remove the test file
            os.remove("dummytemplate2_download.html")

            #
            # Test overwriting the template file with save method
            # Use open(...)
            #

            with open(dummytemplate) as template_upload:
                newlabel2.save(data=None, label=template_upload)

            # Try to download the template file
            newlabel2.downloadTemplate(destination="dummytemplate_download.html")

            self.assertTrue(comparefiles("dummytemplate_download.html", dummytemplate))

            # Remove the test file
            os.remove("dummytemplate_download.html")

    def test_label_printing(self):
        """
        Tests for using label printing function to download PDF files
        """

        # For each class supporting printing, find a related object
        # Define a file, write the label to this file
        # Check for file

        # Parts
        # Object and label - get first in list
        prt = Part.list(self.api)[0]
        lbl_part = LabelPart.list(self.api)[0]

        # Attempt to print to file - use label object
        self.assertTrue(prt.printlabel(label=lbl_part, plugin=None, destination="partlabel_1.pdf"))

        # Attempt to print to file - use label ID directly
        self.assertTrue(prt.printlabel(label=lbl_part.pk, plugin=None, destination="partlabel_2.pdf"))

        # Make sure the files exist
        self.assertTrue(os.path.isfile("partlabel_1.pdf"))
        self.assertTrue(os.path.isfile("partlabel_2.pdf"))
        os.remove("partlabel_1.pdf")
        os.remove("partlabel_2.pdf")

        # StockItem
        # Object and label - get first in list
        sti = StockItem.list(self.api)[0]
        lbl_sti = LabelStock.list(self.api)[0]

        # Attempt to print to file - use label object
        sti.printlabel(label=lbl_sti, plugin=None, destination="stocklabel_1.pdf")
        # Attempt to print to file - use label ID directly
        sti.printlabel(label=lbl_sti.pk, plugin=None, destination="stocklabel_2.pdf")

        # Make sure the files exist
        self.assertTrue(os.path.isfile("stocklabel_1.pdf"))
        self.assertTrue(os.path.isfile("stocklabel_2.pdf"))
        os.remove("stocklabel_1.pdf")
        os.remove("stocklabel_2.pdf")

        # StockLocation
        # Object and label - get first in list
        sloc = StockLocation.list(self.api)[0]
        lbl_sloc = LabelLocation.list(self.api)[0]

        # Attempt to print to file - use label object
        sloc.printlabel(label=lbl_sloc, plugin=None, destination="locationlabel_1.pdf")
        # Attempt to print to file - use label ID directly
        sloc.printlabel(label=lbl_sloc.pk, plugin=None, destination="locationlabel_2.pdf")

        # Make sure the files exist
        self.assertTrue(os.path.isfile("locationlabel_1.pdf"))
        self.assertTrue(os.path.isfile("locationlabel_2.pdf"))
        os.remove("locationlabel_1.pdf")
        os.remove("locationlabel_2.pdf")
