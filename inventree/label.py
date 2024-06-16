# -*- coding: utf-8 -*-

import logging
import os

import inventree.base

logger = logging.getLogger('inventree')


class LabelPrintingMixin:
    """Mixin class for label printing."""

    LABELNAME = ''
    LABELITEM = ''

    def getTemplateId(self, template):
        """Return the ID (pk) from the supplied template."""

        if type(template) in [str, int]:
            return int(template)
        
        if hasattr(template, 'pk'):
            return int(template.pk)
        
        raise ValueError(f"Provided label template is not a valid type: {type(template)}")

    def saveOutput(self, output, filename):
        """Save the output from a label printing job to the specified file path."""

        if os.path.exists(filename) and os.path.isdir(filename):
            filename = os.path.join(
                filename,
                f'Label_{self.getModelType()}_{self.pk}.pdf'
            )
        
        return self._api.downloadFile(url=output, destination=filename)

    def printLabel(self, template, plugin=None, destination=None, *args, **kwargs):
        """Print a label against the provided label template."""

        print_url = '/label/print/'

        template_id = self.getTemplateId(template)

        data = {
            'template': template_id,
            'items': [self.pk]
        }

        if plugin is not None:
            # For the modern printing API, plugin is provided as a key (string) value
            if type(plugin) is str:
                pass
            elif hasattr(plugin, 'key'):
                plugin = plugin.key
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

        try:
            response = super().create(api, data=data, files={'template': label}, **kwargs)
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


class LabelTemplate(LabelFunctions):
    """Class representing the LabelTemplate database model."""

    URL = 'label/template'

    def __str__(self):
        """String representation of the LabelTemplate instance."""

        return f"LabelTemplate <{self.pk}>: '{self.name}' - ({self.model_type})"
