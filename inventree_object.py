import json


class InventreeObject():
    """ Base class for an InvenTree object """

    URL = ""

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

    @staticmethod
    def get_part_list(api, **kwargs):
        """ Return a list of Part objects, using the following filters:

        Args:
            api - InvenTree API object

            category - Filter by part category ID
            buildable - Can this part be built from other parts?
            purchaseable - Can this part be purcahsed from suppliers?
        """

        params = {
        }

        for arg in ['category', 'buildable', 'purchaseable']:
            if kwargs.get(arg, None):
                params[arg] = kwargs[arg]

        response = api.get(Part.URL, params=params, **kwargs)

        parts = []

        if response is None:
            return parts

        for data in response:
            if data and 'pk' in data:
                parts.append(Part(data=data, api=api))

        return parts


    def get_supplier_parts(self):

        response = self._api.get(
            SupplierPart.URL,
            params={
                'part': self['pk']
            })

        parts = []

        if response is None:
            return parts

        for part in response:
            if 'pk' in part.keys():
                parts.append(SupplierPart(data=part, requester=self._requester))

        return parts

    
class SupplierPart(InventreeObject):
    """ Class for maniuplating a SupplierPart object """

    URL = 'company/part'

    @staticmethod
    def get_supplier_part_list(api, **kwargs):
        """ Return a list of supplier part, with the following optional filters:

        Args:
            part - Filter by base part ID
            supplier - Filter by supplier ID
        """

        params = {}

        for arg in ['part', 'supplier']:
            if kwargs.get(arg, None):
                params[arg] = kwargs[arg]

        response = api.get(SupplierPart.URL, params=params, **kwargs)

        parts = []

        if response is None:
            return parts

        for data in response:
            if 'pk' in data:
                parts.append(SupplierPart(data=data, api=api))

        return parts

    def get_price_breaks(self):
        """ Get a list of price break objects for this SupplierPart """

        response = self._api.get(
            SupplierPriceBreak.URL,
            params={
                'part': self['pk']
            })

        breaks = []

        for brk in response:
            if 'pk' in brk.keys():
                breaks.append(SupplierPriceBreak(self._api, data=brk))

        return breaks


class SupplierPriceBreak(InventreeObject):

    URL = 'company/price-break/'