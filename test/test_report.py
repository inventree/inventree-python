# -*- coding: utf-8 -*-

import os
import sys

sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from test_api import InvenTreeTestCase  # noqa: E402
from inventree.part import BomItem  # noqa: E402
from inventree.build import Build  # noqa: E402
from inventree.purchase_order import PurchaseOrder  # noqa: E402
from inventree.sales_order import SalesOrder  # noqa: E402
from inventree.return_order import ReturnOrder  # noqa: E402
from inventree.stock import StockLocation, StockItemTestResult  # noqa: E402
from inventree.report import (ReportBoM, ReportBuild, ReportPurchaseOrder, ReportSalesOrder, ReportReturnOrder, ReportStockLocation, ReportTest)  # noqa: E402


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
