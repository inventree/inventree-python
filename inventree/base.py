# -*- coding: utf-8 -*-

import os
import logging
import json


INVENTREE_PYTHON_VERSION = "0.7.1"


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

    def __init__(self, api, pk=None, data=None):
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
        elif type(pk) is not int:
            raise TypeError(f"Supplied <pk> value ({pk}) for {self.__class__} is invalid.")
        elif pk <= 0:
            raise ValueError(f"Supplier <pk> value ({pk}) for {self.__class__} must be positive.")

        self._url = f"{self.URL}/{pk}/"
        self._api = api

        if data is None:
            data = {}

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
    
    def is_valid(self):
        """
        Test if this object is 'valid' - it has received data from the server.

        To be considered 'valid':

        - Must have a non-null PK
        - Must have a non-null and non-empty data structure
        """

        data = getattr(self, '_data', None)

        if self.pk is None:
            return False

        if data is None:
            return False
        
        if len(data) == 0:
            return False
        
        return True

    def reload(self):
        """ Reload object data from the database """
        if self._api:
            data = self._api.get(self._url)

            if data is None:
                logger.error(f"Error during reload at {self._url}")
            else:
                self._data = data

            if not self.is_valid():
                logger.error(f"Error during reload at {self._url} - returned data is invalid")

        else:
            raise ValueError(f"model.reload failed at '{self._url}': No API instance provided")

    def __getattr__(self, name):
        if name in self._data.keys():
            return self._data[name]
        else:
            return super().__getattr__(name)

    def __getitem__(self, name):
        if name in self._data.keys():
            return self._data[name]
        else:
            raise KeyError(f"Key '{name}' does not exist in dataset")

    def __setitem__(self, name, value):
        if name in self._data.keys():
            self._data[name] = value
        else:
            raise KeyError(f"Key '{name}' does not exist in dataset")


class Attachment(InventreeObject):
    """
    Class representing a file attachment object
    
    Multiple sub-classes exist, representing various types of attachment models in the database
    """

    # List of required kwargs required for the particular subclass
    REQUIRED_KWARGS = []

    @classmethod
    def upload(cls, api, attachment, comment='', **kwargs):
        """
        Upload a file attachment.
        Ref: https://2.python-requests.org/en/master/user/quickstart/#post-a-multipart-encoded-file

        Args:
            api: Authenticated InvenTree API instance
            attachment: Either a file object, or a filename (string)
            comment: Add comment to the upload
            kwargs: Additional kwargs to supply
        """

        data = kwargs
        data['comment'] = comment

        # Check that the extra kwargs are provided
        for arg in cls.REQUIRED_KWARGS:
            if arg not in kwargs:
                raise ValueError(f"Required argument '{arg}' not supplied to upload method")

        if type(attachment) is str:
            if not os.path.exists(attachment):
                raise FileNotFoundError(f"Attachment file '{attachment}' does not exist")

            # Load the file as an in-memory file object
            with open(attachment, 'rb') as fo:

                response = api.post(
                    cls.URL,
                    data,
                    files={
                        'attachment': (os.path.basename(attachment), fo),
                    }
                )
        
        else:
            # Assumes a StringIO or BytesIO like object
            name = getattr(attachment, 'name', 'filename')
            response = api.post(
                cls.URL,
                data,
                files={
                    'attachment': (name, attachment),
                }
            )

        if response:
            logger.info(f"File uploaded to {cls.URL}")
        else:
            logger.error(f"File upload failed at {cls.URL}")
        
        return response

    def download(self, destination, **kwargs):
        """
        Download the attachment file to the specified location
        """

        return self._api.downloadFile(self.attachment, destination, **kwargs)


class Currency(InventreeObject):
    """ Class representing the Currency database model """

    URL = 'common/currency'


class ImageMixin:
    """
    Mixin class for supporting image upload against a model,
    which has a specific 'image' field associated
    """

    def uploadImage(self, image):
        """
        Upload an image against this model.

        Args:
            image: Either an image file (BytesIO) or a filename path
        """

        files = {}

        # string image = filename
        if type(image) is str:
            if os.path.exists(image):
                f = os.path.basename(image)

                with open(image, 'rb') as fo:
                    files['image'] = (f, fo)

                    return self.save(
                        data={},
                        files=files
                    )
            else:
                raise FileNotFoundError(f"Image file does not exist: '{image}'")

        # TODO: Support upload of in-memory images (e.g. Image / BytesIO)

        else:
            raise TypeError(f"uploadImage called with invalid image: '{image}'")

    def downloadImage(self, destination, **kwargs):
        """
        Download the image for this Part, to the specified destination
        """

        if self.image:
            return self._api.downloadFile(self.image, destination, **kwargs)
        else:
            raise ValueError(f"Part '{self.name}' does not have an associated image")
