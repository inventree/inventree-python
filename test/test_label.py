# -*- coding: utf-8 -*-

import os
# ~ import requests
import sys

# ~ from requests.exceptions import HTTPError

# ~ try:
    # ~ import Image
# ~ except ImportError:
    # ~ from PIL import Image

sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from test_api import InvenTreeTestCase  # noqa: E402

from inventree.label import LabelPart, LabelStock, LabelLocation
from inventree.part import Part
from inventree.stock import StockItem, StockLocation


class LabelTest(InvenTreeTestCase):
    """Tests for Label functions models"""

    def test_label_list(self):
        """
        Test for using listing functionality of each type of label
        """

        # Get label list
        lbl_part_list = LabelPart.list(self.api)

        # Make a new list filtered by LabelPart
        # List should be non-zero length
        # Filtered list should be equal the original list
        lbl_part_list_filtered = [x for x in lbl if isinstance(x,LabelPart)]

        self.assertGreater(len(lbl_part_list_filtered), 0)
        self.assertEqual(lbl_part_list,lbl_part_list_filtered)

    def test_label_printing(self):
        """
        Tests for using label printing function to download PDF files
        """

        # For each class supporting printing, find a related object
        # Define a file, write the label to this file
        # Check for file

        # Part and label - get first in list
        prt = Part.list(self.api)[0]
        lbl_part = LabelPart.list(self.api)[0]

        # Attempt to print to file - use label object
        prt.printlabel(label=lbl_part, plugin=None, destination="partlabel_1.pdf");
        # Attempt to print to file - use label ID directly
        prt.printlabel(label=lbl_part.pk, plugin=None, destination="partlabel_2.pdf");

        # Make sure the files exist
        self.assertTrue(os.path.isfile("partlabel_1.pdf"))
        self.assertTrue(os.path.isfile("partlabel_2.pdf"))

        # StockItem
        # StockLocation
        #