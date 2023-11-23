# -*- coding: utf-8 -*-

import logging
import os

import inventree.base

logger = logging.getLogger('inventree')


class LabelPrintingMixin:
    """Mixin class for label printing.

    Classes which implement this mixin should define the following attributes:

    LABELNAME: The name of the label type (e.g. 'part', 'stock', 'location')
    LABELITEM: The name of the label item (e.g. 'parts', 'items', 'locations')
    """

    LABELNAME = ''
    LABELITEM = ''

    def printlabel(self, label, plugin=None, destination=None, *args, **kwargs):
        """Print the label belonging to the given item.

        Set the label with 'label' argument, as the ID of the corresponding
        label. A corresponding label object can also be given.

        If a plugin is given, the plugin will determine
        how the label is printed, and a message is returned.

        Otherwise, if a destination is given, the file will be downloaded to 'destination'.
        Use overwrite=True to overwrite an existing file.

        If neither plugin nor destination is given, nothing will be done
        """

        if isinstance(label, (LabelPart, LabelStock, LabelLocation)):
            label_id = label.pk
        else:
            label_id = label

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


class LabelLocation(inventree.base.MetadataMixin, inventree.base.InventreeObject):
    """ Class representing the Label/Location database model """

    URL = 'label/location'


class LabelPart(inventree.base.MetadataMixin, inventree.base.InventreeObject):
    """ Class representing the Label/Part database model """

    URL = 'label/part'


class LabelStock(inventree.base.MetadataMixin, inventree.base.InventreeObject):
    """ Class representing the Label/stock database model """

    URL = 'label/stock'
