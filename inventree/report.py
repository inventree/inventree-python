# -*- coding: utf-8 -*-

import inventree.base


class ReportPrintingMixin:
    """Mixin class for report printing.

    Classes which implement this mixin should define the following attributes:

    REPORTNAME: The name of the report type, as given in the API (e.g. 'bom', 'build', 'po')
    See https://demo.inventree.org/api-doc/#tag/report
    REPORTITEM: The name of items send to the report print endpoint.
    This is the name of the array of items expected.

    Example:
    https://demo.inventree.org/api/report/test/?item[]=205
        -> REPORTNAME = test
        -> REPORTITEM = item
    """

    REPORTNAME = ''
    REPORTITEM = ''

    def printreport(self, report, destination, *args, **kwargs):
        """Print the report belonging to the given item.

        Set the report with 'report' argument, as the ID of the corresponding
        report. A corresponding report object can also be given.

        The file will be downloaded to 'destination'.
        Use overwrite=True to overwrite an existing file.

        If neither plugin nor destination is given, nothing will be done
        """

        if isinstance(report, (ReportBoM, ReportBuild, ReportPurchaseOrder, ReportSalesOrder, ReportReturnOrder, ReportStockLocation, ReportTest)):
            report_id = report.pk
        else:
            report_id = report

        # Set URL to use
        URL = f'/api/report/{self.REPORTNAME}/{report_id}/print/'

        params = {
            f'{self.REPORTITEM}[]': self.pk
        }

        # Use downloadFile method to get the file
        return self._api.downloadFile(url=URL, destination=destination, params=params, *args, **kwargs)


class ReportBoM(inventree.base.MetadataMixin, inventree.base.InventreeObject):
    """Class representing ReportBoM"""

    URL = 'report/bom'


class ReportBuild(inventree.base.MetadataMixin, inventree.base.InventreeObject):
    """Class representing ReportBuild"""

    URL = 'report/build'


class ReportPurchaseOrder(inventree.base.MetadataMixin, inventree.base.InventreeObject):
    """Class representing ReportPurchaseOrder"""

    URL = 'report/po'


class ReportSalesOrder(inventree.base.MetadataMixin, inventree.base.InventreeObject):
    """Class representing ReportSalesOrder"""

    URL = 'report/so'


class ReportReturnOrder(inventree.base.MetadataMixin, inventree.base.InventreeObject):
    """Class representing ReportReturnOrder"""

    URL = 'report/ro'


class ReportStockLocation(inventree.base.MetadataMixin, inventree.base.InventreeObject):
    """Class representing ReportStockLocation"""

    URL = 'report/slr'


class ReportTest(inventree.base.MetadataMixin, inventree.base.InventreeObject):
    """Class representing ReportTest"""

    URL = 'report/test'
