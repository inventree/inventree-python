# -*- coding: utf-8 -*-

import logging
import os

import inventree.base

logger = logging.getLogger('inventree')

# The InvenTree API endpoint changed considerably @ version 197
# Ref: https://github.com/inventree/InvenTree/pull/7074
MODERN_LABEL_PRINTING_API = 197


class LabelPrintingMixin:
    """Mixin class for label printing.

    Classes which implement this mixin should define the following attributes:

    LABELNAME: The name of the label type (e.g. 'part', 'stock', 'location')
    LABELITEM: The name of the label item (e.g. 'parts', 'items', 'locations')
    """

    LABELNAME = ''
    LABELITEM = ''

    MODEL_TYPE = None

    @classmethod
    def getModelType(cls):
        """Return the model type for this label printing class."""
        return cls.MODEL_TYPE or cls.LABELNAME

    def printlabel(self, label=None, plugin=None, destination=None, *args, **kwargs):
        """Print a label for the given item.

        Check the connected API version to determine if the "modern" or "legacy" approach should be used.
        """

        if self._api.api_version < MODERN_LABEL_PRINTING_API:
            return self.printLabelLegacy(label, plugin=plugin, destination=destination, *args, **kwargs)
        else:
            return self.printLabelModern(label, plugin=plugin, destination=destination, *args, **kwargs)

    def printLabelLegacy(self, label, plugin=None, destination=None, *args, **kwargs):
        """Print the label belonging to the given item.

        Set the label with 'label' argument, as the ID of the corresponding
        label. A corresponding label object can also be given.

        If a plugin is given, the plugin will determine
        how the label is printed, and a message is returned.

        Otherwise, if a destination is given, the file will be downloaded to 'destination'.
        Use overwrite=True to overwrite an existing file.

        If neither plugin nor destination is given, nothing will be done.

        Note: This legacy API support will be deprecated at some point in the future.
        """
        
        if isinstance(label, (LabelPart, LabelStock, LabelLocation)):
            label_id = label.pk
        else:
            try:
                label_id = int(label)
            except ValueError:
                raise ValueError("Invalid label ID provided")

        # Set URL to use
        URL = f'/label/{self.LABELNAME}/{label_id}/print/'

        params = {
            f'{self.LABELITEM}[]': self.pk
        }

        if plugin is not None:
            # Append profile
            params['plugin'] = plugin

        # If API version less than 130, file download is provided directly
        if self._api.api_version < 130 and plugin is None:
            # Ensure we prefix the URL with '/api'
            download_url = f"/api{URL}"
        else:
            # Perform API request, get response
            response = self._api.get(URL, params=params)
            download_url = response.get('file', None)

        # Label file is available for download
        if download_url and destination is not None:
            if os.path.exists(destination) and os.path.isdir(destination):
                # No file name given, construct one
                # Otherwise, filename will be something like '?parts[]=37'
                destination = os.path.join(
                    destination,
                    f'Label_{self.LABELNAME}{label}_{self.pk}.pdf'
                )

            # Use downloadFile method to get the file
            return self._api.downloadFile(url=download_url, destination=destination, params=params, *args, **kwargs)

        else:
            return response

    def printLabelModern(self, template, plugin=None, destination=None, *args, **kwargs):
        """Print a label against the provided label template."""

        print_url = '/api/label/print/'

        # Extract template ID


    def getLabelTemplates(self, **kwargs):
        """Return a list of label templates for this model class."""

        if self._api.api_version < MODERN_LABEL_PRINTING_API:
            logger.error("Legacy label printing API is not supported")
            return []

        return LabelTemplate.list(
            self._api,
            model_type=self.getModelType(),
            **kwargs
        )

class LabelFunctions(inventree.base.MetadataMixin, inventree.base.InventreeObject):
    """Base class for label functions."""

    @classmethod
    def create(cls, api, data, label, **kwargs):
        """Create a new label by uploading a label template file. Convenience wrapper around base create() method.

        Args:
            data: Dict of data including at least name and description for the template
            label: Either a string (filename) or a file object
        """

        # POST endpoints for creating new reports were added in API version 156
        cls.MIN_API_VERSION = 156

        try:
            # If label is already a readable object, don't convert it
            if label.readable() is False:
                raise ValueError("Label template file must be readable")
        except AttributeError:
            label = open(label)
            if label.readable() is False:
                raise ValueError("Label template file must be readable")

        try:
            response = super().create(api, data=data, files={'label': label}, **kwargs)
        finally:
            if label is not None:
                label.close()
        return response

    def save(self, data=None, label=None, **kwargs):
        """Save label to database. Convenience wrapper around save() method.

        Args:
            data (optional): Dict of data to change for the template.
            label (optional): Either a string (filename) or a file object, to upload a new label template
        """

        # PUT/PATCH endpoints for updating data were available before POST endpoints
        self.MIN_API_VERSION = None

        if label is not None:
            try:
                # If template is already a readable object, don't convert it
                if label.readable() is False:
                    raise ValueError("Label template file must be readable")
            except AttributeError:
                label = open(label, 'r')
                if label.readable() is False:
                    raise ValueError("Label template file must be readable")

            if 'files' in kwargs:
                files = kwargs.pop('kwargs')
                files['label'] = label
            else:
                files = {'label': label}
        else:
            files = None

        try:
            response = super().save(data=data, files=files)
        finally:
            if label is not None:
                label.close()
        return response

    def downloadTemplate(self, destination, overwrite=False):
        """Download template file for the label to the given destination"""

        # Use downloadFile method to get the file
        return self._api.downloadFile(url=self._data['label'], destination=destination, overwrite=overwrite)


class LabelLocation(LabelFunctions):
    """ Class representing the Label/Location database model """

    URL = 'label/location'
    MAX_API_VERSION = MODERN_LABEL_PRINTING_API - 1


class LabelPart(LabelFunctions):
    """ Class representing the Label/Part database model """

    URL = 'label/part'
    MAX_API_VERSION = MODERN_LABEL_PRINTING_API - 1


class LabelStock(LabelFunctions):
    """ Class representing the Label/stock database model """

    URL = 'label/stock'
    MAX_API_VERSION = MODERN_LABEL_PRINTING_API - 1


class LabelTemplate(LabelFunctions):
    """Class representing the LabelTemplate database model."""

    URL = 'label/template'
    MIN_API_VERSION = MODERN_LABEL_PRINTING_API