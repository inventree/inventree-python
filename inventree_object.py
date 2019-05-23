import json


class InventreeObject():
    """ Base class for an InvenTree object """

    URL = ""
    FILTERS = []

    def __init__(self, api, pk=None, data={}):
        """ Insantiate this InvenTree object.

        Args:
            pk - The ID (primary key) associated with this object on the server
            api - The request manager object
            data - JSON representation of the object
        """

        # If the pk is not explicitly provided,
        # extract it from the provided dataset
        if pk is None:
            pk = data['pk']

        self._url = "{url}/{pk}/".format(url=self.URL, pk=pk)
        self._api = api
        self._data = data

        # If the data are not populated, fetch from server
        if len(self._data) == 0:
            self.reload()

    @classmethod
    def list(cls, api, **kwargs):
        """ Return a list of all items in this class on the database.

        Requires:

        URL - Base URL
        FILTERS - List of available query filter params
        """

        # Dict of query params to send to the API
        params = {}

        for arg in cls.FILTERS:
            if kwargs.get(arg, None):
                params[arg] = kwargs[arg]

        response = api.get(cls.URL, params=params, **kwargs)

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
            self._api.delete(self._url)

    def save(self):
        """ Save this object to the database """
        if self._api:
            # TODO
            pass

    def reload(self):
        """ Reload object data from the database """
        if self._api:
            data = self._api.get(self._url)
            if data is not None:
                self._data = data

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


class Part(InventreeObject):
    """ Class for manipulating a Part object """

    URL = 'part'
    FILTERS = ['category', 'buildable', 'purchaseable']

    def get_supplier_parts(self):
        return SupplierPart.list(self._api, part=self['pk'])

    def get_bom_items(self):
        return BomItem.list(self._api, part=self['pk'])


class Company(InventreeObject):
    """ Class for manipulating a Company object """

    URL = 'company'
    FILTERS = ['is_supplier', 'is_customer']


class SupplierPart(InventreeObject):
    """ Class for maniuplating a SupplierPart object """

    URL = 'company/part'
    FILTERS = ['part', 'supplier']

    def get_price_breaks(self):
        """ Get a list of price break objects for this SupplierPart """

        return SupplierPriceBreak.list(self._api, part=self['pk'])


class SupplierPriceBreak(InventreeObject):

    URL = 'company/price-break/'
    FILTERS = ['part']


class BomItem(InventreeObject):

    URL = 'bom'
    FILTERS = ['part', 'sub_part']