# -*- coding: utf-8 -*-

import inventree.base


# The InvenTree API endpoint changed considerably @ version 197
# Ref: https://github.com/inventree/InvenTree/pull/7074
MODERN_LABEL_PRINTING_API = 201


class ReportPrintingMixin:
    """Mixin class for report printing.

    Classes which implement this mixin should define the following attributes:

    Legacy API:
        - REPORTNAME: The name of the report type, as given in the API (e.g. 'bom', 'build', 'po')
        - REPORTITEM: The name of items send to the report print endpoint.
        
    Modern API: >= 198
        - MODEL_TYPE: The model type of the report (e.g. 'purchaseorder', 'stocklocation')
    """

    REPORTNAME = ''
    REPORTITEM = ''

    def getTemplateId(self, template):
        """Return the ID (pk) from the supplied template."""

        if type(template) in [str, int]:
            return int(template)
        
        if hasattr(template, 'pk'):
            return int(template.pk)
        
        raise ValueError(f"Provided report template is not a valid type: {type(template)}")

    def printReport(self, report, destination=None, *args, **kwargs):
        """Print the report belonging to the given item.

        Set the report with 'report' argument, as the ID of the corresponding
        report. A corresponding report object can also be given.

        The file will be downloaded to 'destination'.
        Use overwrite=True to overwrite an existing file.

        If neither plugin nor destination is given, nothing will be done
        """

        if self._api.api_version < MODERN_LABEL_PRINTING_API:
            return self.printReportLegacy(report, destination, *args, **kwargs)

        print_url = '/report/print/'
        template_id = self.getTemplateId(report)

        response = self._api.post(
            print_url,
            {
                'template': template_id,
                'items': [self.pk],
            }
        )

        output = response.get('output', None)

        if output and destination:
            return self._api.downloadFile(url=output, destination=destination, *args, **kwargs)
        else:
            return response

    def printReportLegacy(self, report, destination, *args, **kwargs):
        """Print the report template against the legacy API."""

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

    def getReportTemplates(self, **kwargs):
        """Return a list of report templates which match this model class."""

        return ReportTemplate.list(self._api, model_type=self.MODEL_TYPE, **kwargs)


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
        cls.MIN_API_VERSION = 156

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
        self.MIN_API_VERSION = None

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


class ReportTemplate(ReportFunctions):
    """Class representing the ReportTemplatel model."""

    URL = 'report/template'
    MIN_API_VERSION = MODERN_LABEL_PRINTING_API


class ReportBoM(ReportFunctions):
    """Class representing ReportBoM"""

    URL = 'report/bom'
    MAX_API_VERSION = MODERN_LABEL_PRINTING_API


class ReportBuild(ReportFunctions):
    """Class representing ReportBuild"""

    URL = 'report/build'
    MAX_API_VERSION = MODERN_LABEL_PRINTING_API


class ReportPurchaseOrder(ReportFunctions):
    """Class representing ReportPurchaseOrder"""

    URL = 'report/po'
    MAX_API_VERSION = MODERN_LABEL_PRINTING_API


class ReportSalesOrder(ReportFunctions):
    """Class representing ReportSalesOrder"""

    URL = 'report/so'
    MAX_API_VERSION = MODERN_LABEL_PRINTING_API


class ReportReturnOrder(ReportFunctions):
    """Class representing ReportReturnOrder"""

    URL = 'report/ro'
    MAX_API_VERSION = MODERN_LABEL_PRINTING_API


class ReportStockLocation(ReportFunctions):
    """Class representing ReportStockLocation"""

    # The Stock location report was added when API version was 127, but the API version was not incremented at the same time
    # The closest API version which has the SLR report is 128
    MIN_API_VERSION = 128
    URL = 'report/slr'
    MAX_API_VERSION = MODERN_LABEL_PRINTING_API


class ReportTest(ReportFunctions):
    """Class representing ReportTest"""

    URL = 'report/test'
    MAX_API_VERSION = MODERN_LABEL_PRINTING_API
