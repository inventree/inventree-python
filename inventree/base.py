# -*- coding: utf-8 -*-

import os
import logging
import json


INVENTREE_PYTHON_VERSION = "0.4.4"


logger = logging.getLogger('inventree')


class InventreeObject(object):
    """ Base class for an InvenTree object """

    URL = ""

    def __str__(self):
        """
        Simple human-readable printing.
        Can override in subclass
        """

        return f"{type(self)}<pk={self.pk}>"

    def __init__(self, api, pk=None, data={}):
        """ Instantiate this InvenTree object.

        Args:
            pk - The ID (primary key) associated with this object on the server
            api - The request manager object
            data - JSON representation of the object
        """

        # If the pk is not explicitly provided,
        # extract it from the provided dataset
        if pk is None:
            pk = data.get('pk', None)

        self._url = "{url}/{pk}/".format(url=self.URL, pk=pk)
        self._api = api
        self._data = data

        # If the data are not populated, fetch from server
        if len(self._data) == 0:
            self.reload()

    @classmethod
    def fields(cls, api):
        """
        Returns a list of available fields for this model.

        Introspects the available fields using an OPTIONS request.
        """

        response = api.request(
            cls.URL,
            method='options',
        )

        if not response.status_code == 200:
            logger.error(f"OPTIONS for '{cls.URL}' returned code {response.status_code}")
            return {}

        try:
            data = json.loads(response.text)
        except json.decoder.JSONDecodeError:
            logger.error(f"Error decoding JSON response for '{cls.URL}'")
            return {}

        actions = data.get('actions', {})
        post = actions.get('POST', {})

        return post

    @classmethod
    def fieldNames(cls, api):
        """
        Return a list of available field names for this model
        """

        return [k for k in cls.fields(api).keys()]

    @property
    def pk(self):
        """ Convenience method for accessing primary-key field """
        return self._data.get('pk', None)

    @classmethod
    def create(cls, api, data, **kwargs):
        """ Create a new database object in this class. """

        # Ensure the pk value is None so an existing object is not updated
        if 'pk' in data.keys():
            data.pop('pk')

        response = api.post(cls.URL, data)
        
        if response is None:
            logger.error("Error creating new object")
            return None

        return cls(api, data=response)

    @classmethod
    def list(cls, api, **kwargs):
        """ Return a list of all items in this class on the database.

        Requires:

        URL - Base URL
        """

        # Dict of query params to send to the API
        params = kwargs

        # Check if custom URL is present in request arguments
        if 'url' in kwargs:
            url = kwargs.pop('url')
        else:
            url = cls.URL

        response = api.get(url=url, params=params, **kwargs)

        if response is None:
            return None

        items = []

        for data in response:
            if 'pk' in data:
                items.append(cls(data=data, api=api))

        return items

    def delete(self):
        """ Delete this object from the database """
        if self._api:
            return self._api.delete(self._url)

    def save(self, data=None, files=None, method='PATCH'):
        """
        Save this object to the database
        """
        
        # If 'data' is not specified, then use *all* the data
        if data is None:
            data = self._data
        
        if self._api:
            
            # Default method used is PATCH (partial update)
            if method.lower() == 'patch':
                response = self._api.patch(self._url, data, files=files)
            elif method.lower() == 'put':
                response = self._api.put(self._url, data, files=files)
            else:
                logger.warning(f"save() called with unknown method '{method}'")
                return

        # Automatically re-load data from the returned data
        if response is not None:
            self._data = response
        else:
            self.reload()

        return response

    def reload(self):
        """ Reload object data from the database """
        if self._api:
            data = self._api.get(self._url)
            if data is not None:
                self._data = data

    def __getattr__(self, name):
        if name in self._data.keys():
            return self._data[name]
        else:
            return super().__getattr__(name)

    def __getitem__(self, name):
        if name in self._data.keys():
            return self._data[name]
        else:
            raise KeyError("Key '{k}' does not exist in dataset".format(k=name))

    def __setitem__(self, name, value):
        if name in self._data.keys():
            self._data[name] = value
        else:
            raise KeyError("Key '{k}' does not exist in dataset".format(k=name))


class Attachment(InventreeObject):
    """ Class representing a file attachment object """

    @classmethod
    def upload(cls, api, filename, comment, **kwargs):
        """
        Upload a file attachment.
        Ref: https://2.python-requests.org/en/master/user/quickstart/#post-a-multipart-encoded-file
        """

        if not os.path.exists(filename):
            logger.error("File does not exist: '{f}'".format(f=filename))
            return

        f = os.path.basename(filename)

        data = kwargs

        # File comment must be provided
        data['comment'] = comment

        files = {
            'attachment': (f, open(filename, 'rb')),
        }

        # Send the file off to the server
        response = api.post(cls.URL, data, files=files)

        if response:
            logger.info("Uploaded attachment file: '{f}'".format(f=f))
        else:
            logger.warning("File upload failed")

    def download(self, destination):
        """
        Download the attachment file to the specified location
        """

        return self._api.downloadFile(self.attachment, destination)


class Currency(InventreeObject):
    """ Class representing the Currency database model """

    URL = 'common/currency'


class Parameter(InventreeObject):
    """class representing the Parameter database model """
    URL = 'part/parameter'

    def getunits(self):
        """ Get the dimension and units for this parameter """

        return [element for element
                in ParameterTemplate.list(self._api)
                if element['pk'] == self._data['template']]


class ParameterTemplate(InventreeObject):
    """ class representing the Parameter Template database model"""

    URL = 'part/parameter/template'
