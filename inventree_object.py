""" This module provides class-based accessors for InvenTree database models,
using the integrated REST API.
"""


class InventreeObject():
    """ Base class for an InvenTree object """

    URL = ""
    FILTERS = []

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
            pk = data['pk']

        self._url = "{url}/{pk}/".format(url=self.URL, pk=pk)
        self._api = api
        self._data = data

        # If the data are not populated, fetch from server
        if len(self._data) == 0:
            self.reload()

    @property
    def pk(self):
        """ Convenience method for accessing primary-key field """
        return self['pk']

    @classmethod
    def create(cls, api, data, **kwargs):
        """ Create a new database object in this class. """

        # Ensure the pk value is None so an existing object is not updated
        del data['pk']

        api.post(cls.URL, data)

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
            self._api.put(self._url, self._data)

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


class PartCategory(InventreeObject):
    """ Class representing the PartCategory database model """

    URL = 'part/category'
    FILTERS = ['parent']

    def get_parts(self):
        return Part.list(self._api, category=self.pk)
    

class Part(InventreeObject):
    """ Class representing the Part database model """

    URL = 'part'
    FILTERS = ['category', 'buildable', 'purchaseable']

    def get_supplier_parts(self):
        """ Return the supplier parts associated with this part """
        return SupplierPart.list(self._api, part=self.pk)

    def get_bom_items(self):
        """ Return the items required to make this part """
        return BomItem.list(self._api, part=self.pk)

    def get_builds(self):
        """ Return the builds associated with this part """
        return Build.list(self._api, part=self.pk)

    def get_stock_items(self):
        """ Return the stock items associated with this part """
        return StockItem.list(self._api, part=self.pk)


class StockLocation(InventreeObject):
    """ Class representing the StockLocation database model """

    URL = 'stock/location'
    filters = ['parent']

    def get_stock_items(self):
        return StockItem.list(self._api, location=self.pk)


class StockItem(InventreeObject):
    """ Class representing the StockItem database model.
    
    Stock items can be filtered by:
    
    - location: Where the stock item is stored
    - category: The category of the part this stock item points to
    - supplier: Who supplied this stock item
    - part: The part referenced by this stock item
    - supplier_part: Matching SupplierPart object
    """

    URL = 'stock'
    FILTERS = ['location', 'category', 'supplier', 'part', 'supplier_part']


class Company(InventreeObject):
    """ Class representing the Company database model """

    URL = 'company'
    FILTERS = ['is_supplier', 'is_customer']

    def get_supplier_parts(self):
        return SupplierPart.list(self._api, part=self.pk)


class SupplierPart(InventreeObject):
    """ Class representing the SupplierPart database model """

    URL = 'company/part'
    FILTERS = ['part', 'supplier']

    def get_price_breaks(self):
        """ Get a list of price break objects for this SupplierPart """

        return SupplierPriceBreak.list(self._api, part=self.pk)


class SupplierPriceBreak(InventreeObject):
    """ Class representing the SupplierPriceBreak database model """

    URL = 'company/price-break/'
    FILTERS = ['part', 'currency']


class BomItem(InventreeObject):
    """ Class representing the BomItem database model """

    URL = 'bom'
    FILTERS = ['part', 'sub_part']


class Build(InventreeObject):
    """ Class representing the Build database model """

    URL = 'build'
    FILTERS = ['part']


class Currency(InventreeObject):
    """ Class representing the Currency database model """

    URL = 'common/currency'


class Parameter(InventreeObject):
    """class representing the Parameter database model """
    URL = 'part/parameter'
    FILTERS = ['part']

    def getunits(self):
        """ Get the dimension and units for this parameter """

        return [element for element
                in ParameterTemplate.list(self._api)
                if element['pk'] == self._data['template']]


class ParameterTemplate(InventreeObject):
    """ class representing the Parameter Template database model"""

    URL = 'part/parameter/template'
