# -*- coding: utf-8 -*-

import json
import logging
import os

from . import api as inventree_api

INVENTREE_PYTHON_VERSION = "0.13.1"


logger = logging.getLogger('inventree')


class InventreeObject(object):
    """ Base class for an InvenTree object """

    # API URL (required) for the particular model type
    URL = ""

    # Minimum server version for the particular model type
    REQUIRED_API_VERSION = None

    def __str__(self):
        """
        Simple human-readable printing.
        Can override in subclass
        """

        return f"{type(self)}<pk={self.pk}>"

    def __init__(self, api, pk=None, data=None):
        """ Instantiate this InvenTree object.

        Args:
            api - The request manager object
            pk - The ID (primary key) associated with this object on the server
            data - JSON representation of the object
        """

        self.checkApiVersion(api)

        # If the pk is not explicitly provided,
        # extract it from the provided dataset
        if pk is None and data:
            pk = data.get('pk', None)

        # Convert to integer
        try:
            pk = int(pk)
        except Exception:
            raise TypeError(f"Supplied <pk> value ({pk}) for {self.__class__} is invalid.")

        if pk <= 0:
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
    def checkApiVersion(cls, api):
        """Check if the API version supports this particular model.

        Raises:
            NotSupportedError if the server API version is too 'old'
        """

        if cls.REQUIRED_API_VERSION is not None:
            if cls.REQUIRED_API_VERSION > api.api_version:
                raise NotImplementedError(f"Server API Version ({api.api_version}) is too old for the '{cls.__name__}' class, which requires API version {cls.REQUIRED_API_VERSION}")

    @classmethod
    def options(cls, api):
        """Perform an OPTIONS request for this model, to determine model information.

        InvenTree provides custom metadata for each API endpoint, accessed via a HTTP OPTIONS request.
        This endpoint provides information on the various fields available for that endpoint.
        """

        cls.checkApiVersion(api)

        response = api.request(
            cls.URL,
            method='OPTIONS',
        )

        if not response.status_code == 200:
            logger.error(f"OPTIONS for '{cls.URL}' returned code {response.status_code}")
            return {}

        try:
            data = json.loads(response.text)
        except json.decoder.JSONDecodeError:
            logger.error(f"Error decoding OPTIONS response for '{cls.URL}'")
            return {}

        return data

    @classmethod
    def fields(cls, api):
        """
        Returns a list of available fields for this model.

        Introspects the available fields using an OPTIONS request.
        """

        opts = cls.options(api)

        actions = opts.get('actions', {})
        post = actions.get('POST', {})

        return post

    @classmethod
    def fieldInfo(cls, field_name, api):
        """Return metadata for a specific field on a model"""

        fields = cls.fields(api)

        if field_name in fields:
            return fields[field_name]
        else:
            logger.warning(f"Field '{field_name}' not found in OPTIONS request for {cls.URL}")
            return {}

    @classmethod
    def fieldNames(cls, api):
        """
        Return a list of available field names for this model
        """

        return [k for k in cls.fields(api).keys()]

    @property
    def pk(self):
        """ Convenience method for accessing primary-key field """
        val = self._data.get('pk', None)

        try:
            val = int(val)
        except ValueError:
            pass

        return val

    @classmethod
    def create(cls, api, data, **kwargs):
        """ Create a new database object in this class. """

        cls.checkApiVersion(api)

        # Ensure the pk value is None so an existing object is not updated
        if 'pk' in data.keys():
            data.pop('pk')

        response = api.post(cls.URL, data, **kwargs)

        if response is None:
            logger.error("Error creating new object")
            return None

        return cls(api, data=response)

    @classmethod
    def count(cls, api, **kwargs):
        """Return a count of all items of this class in the database"""

        params = kwargs

        # By limiting to a single result, we perform a fast query, but get a total number of results
        params['limit'] = 1

        response = api.get(url=cls.URL, params=params)

        return response['count']

    @classmethod
    def list(cls, api, **kwargs):
        """Return a list of all items in this class on the database.

        Requires:

        URL - Base URL
        """
        cls.checkApiVersion(api)

        # Check if custom URL is present in request arguments
        if 'url' in kwargs:
            url = kwargs.pop('url')
        else:
            url = cls.URL

        response = api.get(url=url, params=kwargs)

        if response is None:
            return None

        items = []

        if isinstance(response, dict) and response['results'] is not None:
            response = response['results']

        for data in response:
            if 'pk' in data:
                items.append(cls(data=data, api=api))

        return items

    def delete(self):
        """ Delete this object from the database """

        self.checkApiVersion(self._api)

        if self._api:
            return self._api.delete(self._url)

    def save(self, data=None, files=None, method='PATCH'):
        """
        Save this object to the database
        """

        self.checkApiVersion(self._api)

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

        self.checkApiVersion(self._api)

        if self._api:
            data = self._api.get(self._url)

            if data is None:
                logger.error(f"Error during reload at {self._url}")
            else:
                self._data = data

            if not self.is_valid():
                logger.error(f"Error during reload at {self._url} - returned data is invalid")

        else:
            raise AttributeError(f"model.reload failed at '{self._url}': No API instance provided")

    def keys(self):
        return self._data.keys()

    def __contains__(self, name):
        return name in self._data

    def __getattr__(self, name):

        if name in self._data.keys():
            return self._data[name]
        else:
            return super().__getattribute__(name)

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


class BulkDeleteMixin:
    """Mixin class for models which support 'bulk deletion'

    - Perform a DELETE operation against the LIST endpoint for the model
    - Provide a list of items to be deleted, or filters to apply

    Requires API version 58
    """

    @classmethod
    def bulkDelete(cls, api: inventree_api.InvenTreeAPI, items=None, filters=None):
        """Perform bulk delete operation

        Arguments:
            api: InventreeAPI instance
            items: Optional list of items (pk values) to be deleted
            filters: Optional query filters to delete

        Returns:
            API response object

        Throws:
            NotImplementError: The server API version is too old (requires v58)
            ValueError: Neither items or filters are supplied

        """

        if api.api_version < 58:
            raise NotImplementedError("bulkDelete requires API version 58 or newer")

        if not items and not filters:
            raise ValueError("Must supply either 'items' or 'filters' argument")

        data = {}

        if items:
            data['items'] = items

        if filters:
            data['filters'] = filters

        return api.delete(
            cls.URL,
            json=data,
        )


class Attachment(BulkDeleteMixin, InventreeObject):
    """
    Class representing a file attachment object

    Multiple sub-classes exist, representing various types of attachment models in the database.
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


class MetadataMixin:
    """Mixin class for models which support a 'metadata' attribute.

    - The 'metadata' is not used for any InvenTree business logic
    - Instead it can be used by plugins for storing arbitrary information
    - Internally it is stored as a JSON database field
    - Metadata is accessed via the API by appending '/metadata/' to the API URL

    Note: Requires server API version 49 or newer

    """

    @property
    def metadata_url(self):
        return os.path.join(self._url, "metadata/")

    def getMetadata(self):
        """Read model instance metadata"""
        if self._api:

            if self._api.api_version < 49:
                logger.error("API version 49 or newer required to access instance metadata")
                return {}

            response = self._api.get(self.metadata_url)

            return response['metadata']
        else:
            raise AttributeError(f"model.getMetadata failed at '{self._url}': No API instance provided")

    def setMetadata(self, data, overwrite=False):
        """Write metadata to this particular model.

        Arguments:
            data: The data to be written. Must be a dict object
            overwrite: If true, provided data replaces existing data. If false (default) data is merged with any existing data.
        """

        if type(data) is not dict:
            raise TypeError("Data provided to 'setMetadata' method must be a dict object")

        if self._api:

            if self._api.api_version < 49:
                logger.error("API version 49 or newer required to access instance metadata")
                return None

            if overwrite:
                return self._api.put(
                    self.metadata_url,
                    data={
                        "metadata": data,
                    }
                )
            else:
                return self._api.patch(
                    self.metadata_url,
                    data={
                        "metadata": data
                    }
                )
        else:
            raise AttributeError(f"model.setMetadata failed at '{self._url}': No API instance provided")


class ImageMixin:
    """Mixin class for supporting image upload against a model.

    - The model must have a specific 'image' field associated
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


class StatusMixin:
    """Class adding functionality to assign a new status by calling
    - complete
    - cancel
    on supported items.

    Other functions, such as
    - ship
    - finish
    - issue
    can be reached through _statusupdate function
    """

    def _statusupdate(self, status: str, reload=True, data=None, **kwargs):

        # Check status
        if status not in [
            'complete',
            'cancel',
            'ship',
            'issue',
            'finish',
        ]:
            raise ValueError(f"Order stats {status} not supported.")

        # Set the url
        URL = self.URL + f"/{self.pk}/{status}"

        if data is None:
            data = {}

        data.update(kwargs)

        # Send data
        response = self._api.post(URL, data)

        # Reload
        if reload:
            self.reload()

        # Return
        return response

    def complete(self, **kwargs):

        return self._statusupdate(status='complete', **kwargs)

    def cancel(self, **kwargs):

        return self._statusupdate(status='cancel', **kwargs)


class BarcodeMixin:
    """Adds barcode scanning functionality to various data types.

    Any class which inherits from this mixin can assign (or un-assign) barcode data.
    """

    @classmethod
    def barcodeModelType(cls):
        """Return the model type name required for barcode assignment.

        Default value is the lower-case class name ()
        """
        return cls.__name__.lower()

    def assignBarcode(self, barcode_data: str, reload=True):
        """Assign an arbitrary barcode to this object (in the database).

        Arguments:
            barcode_data: A string containing arbitrary barcode data
        """

        model_type = self.barcodeModelType()

        response = self._api.post(
            '/barcode/link/',
            {
                'barcode': barcode_data,
                model_type: self.pk,
            }
        )

        if reload:
            self.reload()

        return response

    def unassignBarcode(self, reload=True):
        """Unassign a barcode from this object"""

        model_type = self.barcodeModelType()

        response = self._api.post(
            '/barcode/unlink/',
            {
                model_type: self.pk,
            }
        )

        if reload:
            self.reload()

        return response
