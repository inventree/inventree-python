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


class ReportFunctions(inventree.base.MetadataMixin, inventree.base.InventreeObject):
    """Base class for report functions"""

    @classmethod
    def create(cls, api, data, template, **kwargs):
        """Create a new report by uploading a template file. Convenience wrapper around base create() method.

        Args:
            data: Dict of data including at least name and description for the template
            template: Either a string (filename) or a file object
        """

        # POST endpoints for creating new reports were added in API version 156
        cls.REQUIRED_API_VERSION = 156

        try:
            # If template is already a readable object, don't convert it
            if template.readable() is False:
                raise ValueError("Template file must be readable")
        except AttributeError:
            template = open(template)
            if template.readable() is False:
                raise ValueError("Template file must be readable")

        try:
            response = super().create(api, data=data, files={'template': template}, **kwargs)
        finally:
            if template is not None:
                template.close()
        return response

    def save(self, data=None, template=None, **kwargs):
        """Save report data to database. Convenience wrapper around save() method.

        Args:
            data (optional): Dict of data to change for the template.
            template (optional): Either a string (filename) or a file object, to upload a new template
        """

        # PUT/PATCH endpoints for updating data were available before POST endpoints
        self.REQUIRED_API_VERSION = None

        if template is not None:
            try:
                # If template is already a readable object, don't convert it
                if template.readable() is False:
                    raise ValueError("Template file must be readable")
            except AttributeError:
                template = open(template, 'r')
                if template.readable() is False:
                    raise ValueError("Template file must be readable")

            if 'files' in kwargs:
                files = kwargs.pop('kwargs')
                files['template'] = template
            else:
                files = {'template': template}
        else:
            files = None

        try:
            response = super().save(data=data, files=files)
        finally:
            if template is not None:
                template.close()
        return response

    def downloadTemplate(self, destination, overwrite=False):
        """Download template file for the report to the given destination"""

        # Use downloadFile method to get the file
        return self._api.downloadFile(url=self._data['template'], destination=destination, overwrite=overwrite)


class ReportBoM(ReportFunctions):
    """Class representing ReportBoM"""

    URL = 'report/bom'


class ReportBuild(ReportFunctions):
    """Class representing ReportBuild"""

    URL = 'report/build'


class ReportPurchaseOrder(ReportFunctions):
    """Class representing ReportPurchaseOrder"""

    URL = 'report/po'


class ReportSalesOrder(ReportFunctions):
    """Class representing ReportSalesOrder"""

    URL = 'report/so'


class ReportReturnOrder(ReportFunctions):
    """Class representing ReportReturnOrder"""

    URL = 'report/ro'


class ReportStockLocation(ReportFunctions):
    """Class representing ReportStockLocation"""

    # The Stock location report was added when API version was 127, but the API version was not incremented at the same time
    # The closest API version which has the SLR report is 128
    REQUIRED_API_VERSION = 128
    URL = 'report/slr'


class ReportTest(ReportFunctions):
    """Class representing ReportTest"""

    URL = 'report/test'
