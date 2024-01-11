# -*- coding: utf-8 -*-

import os
import sys

sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from test_api import InvenTreeTestCase  # noqa: E402

from inventree.build import Build  # noqa: E402
from inventree.part import BomItem  # noqa: E402
from inventree.purchase_order import PurchaseOrder  # noqa: E402
from inventree.report import (ReportBoM, ReportBuild,  # noqa: E402
                              ReportPurchaseOrder, ReportReturnOrder,
                              ReportSalesOrder, ReportStockLocation,
                              ReportTest)
from inventree.return_order import ReturnOrder  # noqa: E402
from inventree.sales_order import SalesOrder  # noqa: E402
from inventree.stock import StockItemTestResult, StockLocation  # noqa: E402


class ReportClassesTest(InvenTreeTestCase):
    """Tests for Report functions models"""

    def test_report_list(self):
        """
        Test for using listing functionality of each type of label
        """

        for RepClass in (ReportBoM, ReportBuild, ReportPurchaseOrder, ReportSalesOrder, ReportReturnOrder, ReportStockLocation, ReportTest):
            # Get report list
            report_list = RepClass.list(self.api)

            # Make a new list filtered by LabelPart
            # List should be non-zero length
            # Filtered list should be equal the original list
            report_list_filtered = [x for x in report_list if isinstance(x, RepClass)]

            self.assertGreater(len(report_list_filtered), 0)
            self.assertEqual(report_list, report_list_filtered)

    def test_report_create_download(self):
        """
        Tests creating a new report from API, by uploading the dummy template file
        """

        dummytemplate = os.path.join(os.path.dirname(__file__), 'dummytemplate.html')
        dummytemplate2 = os.path.join(os.path.dirname(__file__), 'dummytemplate2.html')

        for RepClass in (ReportBoM, ReportBuild, ReportPurchaseOrder, ReportSalesOrder, ReportReturnOrder, ReportStockLocation, ReportTest):
            # Test for all Label classes sequentially

            #
            # Test with file name
            #

            # Create a new label based on the dummy template
            newlabel = RepClass.create(
                self.api,
                {'name': 'Dummy report', 'description': 'Report created as test'},
                dummytemplate
            )

            # The return value should be a LabelPart object
            self.assertTrue(isinstance(newlabel, RepClass))

            # Try to download the template file
            newlabel.downloadTemplate(destination="dummytemplate_download.html")

            # Compare file contents, make sure they're the same
            self.assertListEqual(
                list("dummytemplate_download.html"),
                list(dummytemplate)
            )

            # Remove the test file
            os.remove("dummytemplate_download.html")

            #
            # Test with open(...)
            #

            # Create a new label based on the dummy template
            newlabel2 = RepClass.create(
                self.api,
                {'name': 'Dummy report', 'description': 'Report created as test'},
                open(dummytemplate)
            )

            # The return value should be a LabelPart object
            self.assertTrue(isinstance(newlabel2, RepClass))

            # Try to download the template file
            newlabel2.downloadTemplate(destination="dummytemplate_download.html")

            # Compare file contents, make sure they're the same
            self.assertListEqual(
                list("dummytemplate_download.html"),
                list(dummytemplate)
            )

            # Remove the test file
            os.remove("dummytemplate_download.html")

            #
            # Test overwriting the label file with save method
            # Use file name
            #

            newlabel2.save(data=None, template=dummytemplate2)

            # Try to download the template file
            newlabel2.downloadTemplate(destination="dummytemplate2_download.html")

            # Compare file contents, make sure they're the same
            self.assertListEqual(
                list("dummytemplate2_download.html"),
                list(dummytemplate2)
            )

            # Remove the test file
            os.remove("dummytemplate2_download.html")

            #
            # Test overwriting the template file with save method
            # Use open(...)
            #

            newlabel2.save(data=None, template=open(dummytemplate))

            # Try to download the template file
            newlabel2.downloadTemplate(destination="dummytemplate_download.html")

            # Compare file contents, make sure they're the same
            self.assertListEqual(
                list("dummytemplate_download.html"),
                list(dummytemplate)
            )

            # Remove the test file
            os.remove("dummytemplate_download.html")

    def test_report_printing(self):
        """
        Tests for using report printing function to download PDF files
        """

        # For each class supporting reports, find a related object
        # Define a file, write the label to this file
        # Check for file

        testscount = 0

        for ItemModel, RepClass in zip(
                (BomItem, Build, PurchaseOrder, SalesOrder, ReturnOrder, StockLocation, StockItemTestResult),
                (ReportBoM, ReportBuild, ReportPurchaseOrder, ReportSalesOrder, ReportReturnOrder, ReportStockLocation, ReportTest)
        ):

            # Item and report - get first in list
            itmlist = ItemModel.list(self.api)
            replist = RepClass.list(self.api)

            # The test can only be carried out if there are items and reports defined
            if len(itmlist) > 0 and len(replist) > 0:
                itm = itmlist[0]
                rep = replist[0]

                # Attempt to print to file - use label object
                self.assertTrue(itm.printreport(report=rep, destination="report.pdf"))

                # Make sure the files exist
                self.assertTrue(os.path.isfile("report.pdf"))

                os.remove("report.pdf")

                testscount += 1

        # Make sure we actually tested something
        assert testscount > 0
