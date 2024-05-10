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

    Legacy API: < 197
        - LABELNAME: The name of the label type (e.g. 'part', 'stock', 'location')
        - LABELITEM: The name of the label item (e.g. 'parts', 'items', 'locations')
    
    Modern API: >= 197
        - MODEL_TYPE: The model type for the label printing class (e.g. 'part', 'stockitem', 'location')
    """

    LABELNAME = ''
    LABELITEM = ''

    # Each class should specify the associated 'model_type' attribite - e.g. 'stockitem'
    MODEL_TYPE = None

    @classmethod
    def getModelType(cls):
        """Return the model type for this label printing class."""
        return cls.MODEL_TYPE or cls.LABELNAME

    def getTemplateId(self, template):
        """Return the ID (pk) from the supplied template."""

        if type(template) in [str, int]:
            return int(template)
        
        if hasattr(template, 'pk'):
            return int(template.pk)
        
        raise ValueError(f"Provided template is not a valid type: {type(template)}")

    def saveOutput(self, output, filename):
        """Save the output from a label printing job to the specified file path."""

        if os.path.exists(filename) and os.path.isdir(filename):
            filename = os.path.join(
                filename,
                f'Label_{self.getModelType()}_{self.pk}.pdf'
            )
        
        return self._api.downloadFile(url=output, destination=filename)

    def printLabel(self, label=None, plugin=None, destination=None, *args, **kwargs):
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

        label_id = self.getTemplateId(label)
        
        # Set URL to use
        URL = f'/label/{self.LABELNAME}/{label_id}/print/'

        params = {
            f'{self.LABELITEM}[]': self.pk
        }

        if plugin is not None:

            # For the legacy printing API, plugin is provided as a 'slug' (string)
            if type(plugin) is not str:
                raise TypeError(f"Plugin must be a string, not {type(plugin)}")

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
        if download_url and destination:
            return self.saveOutput(download_url, destination)
            
        else:
            return response

    def printLabelModern(self, template, plugin=None, destination=None, *args, **kwargs):
        """Print a label against the provided label template."""

        print_url = '/label/print/'

        template_id = self.getTemplateId(template)

        data = {
            'template': template_id,
            'items': [self.pk]
        }

        if plugin is not None:
            # For the modern printing API, plugin is provided as a pk (integer) value
            if type(plugin) is int:
                plugin = int(plugin)
            elif hasattr(plugin, 'pk'):
                plugin = int(plugin.pk)
            else:
                raise ValueError(f"Invalid plugin provided: {type(plugin)}")
            
            data['plugin'] = plugin
        
        response = self._api.post(
            print_url,
            data=data
        )

        output = response.get('output', None)

        if output and destination:
            return self.saveOutput(output, destination)
        else:
            return response

    def getLabelTemplates(self, **kwargs):
        """Return a list of label templates for this model class."""

        if self._api.api_version < MODERN_LABEL_PRINTING_API:
            logger.error("Legacy label printing API is not supported")
            return []

        print("getting templates for:", self.getModelType())

        return LabelTemplate.list(
            self._api,
            model_type=self.getModelType(),
            **kwargs
        )


class LabelFunctions(inventree.base.MetadataMixin, inventree.base.InventreeObject):
    """Base class for label functions."""

    @property
    def template_key(self):
        """Return the attribute name for the template file."""

        if self._api.api_version < MODERN_LABEL_PRINTING_API:
            return 'label'
        else:
            return 'template'

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

        template_key = 'template' if api.api_version >= MODERN_LABEL_PRINTING_API else 'label'

        try:
            response = super().create(api, data=data, files={template_key: label}, **kwargs)
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
                files[self.template_key] = label
            else:
                files = {self.template_key: label}
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
        return self._api.downloadFile(url=self._data[self.template_key], destination=destination, overwrite=overwrite)


class LabelLocation(LabelFunctions):
    """Class representing the Label/Location database model.
    
    Note: This class will be deprecated at some point in the future.
    """

    URL = 'label/location'
    MAX_API_VERSION = MODERN_LABEL_PRINTING_API - 1


class LabelPart(LabelFunctions):
    """Class representing the Label/Part database model.
    
    Note: This class will be deprecated at some point in the future.
    """

    URL = 'label/part'
    MAX_API_VERSION = MODERN_LABEL_PRINTING_API - 1


class LabelStock(LabelFunctions):
    """Class representing the Label/stock database model.
    
    Note: This class will be deprecated at some point in the future.
    """

    URL = 'label/stock'
    MAX_API_VERSION = MODERN_LABEL_PRINTING_API - 1


class LabelTemplate(LabelFunctions):
    """Class representing the LabelTemplate database model."""

    URL = 'label/template'
    MIN_API_VERSION = MODERN_LABEL_PRINTING_API

    def __str__(self):
        """String representation of the LabelTemplate instance."""

        return f"LabelTemplate <{self.pk}>: '{self.name}' - ({self.model_type})"
