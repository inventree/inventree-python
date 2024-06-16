# -*- coding: utf-8 -*-

import inventree.base


class ReportPrintingMixin:
    """Mixin class for report printing."""

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

    def getReportTemplates(self, **kwargs):
        """Return a list of report templates which match this model class."""

        return ReportTemplate.list(self._api, model_type=self.getModelType(), **kwargs)


class ReportFunctions(inventree.base.MetadataMixin, inventree.base.InventreeObject):
    """Base class for report functions"""

    @classmethod
    def create(cls, api, data, template, **kwargs):
        """Create a new report by uploading a template file. Convenience wrapper around base create() method.

        Args:
            data: Dict of data including at least name and description for the template
            template: Either a string (filename) or a file object
        """

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
    """Class representing the ReportTemplate model."""

    URL = 'report/template'
