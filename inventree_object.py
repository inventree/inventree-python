import json


class InventreeObject():
    """ Base class for an InvenTree object """

    URL = ""

    def __init__(self, requester, pk=None, data={}):
        """ Insantiate this InvenTree object.

        Args:
            pk - The ID (primary key) associated with this object on the server
            requester - The request manager object
            data - JSON representation of the object
        """

        # If the pk is not explicitly provided,
        # extract it from the provided dataset
        if pk is None:
            pk = data['pk']

        self._url = "{url}/{pk}/".format(url=self.URL, pk=pk)
        self._requester = requester
        self._data = data

        # If the data are not populated, fetch from server
        if len(self._data) == 0:
            self.reload()

    def delete(self):
        """ Delete this object from the database """
        if self._requester:
            self._requester.delete(self._url)

    def save(self):
        """ Save this object to the database """
        if self._requester:
            # TODO
            pass

    def reload(self):
        """ Reload object data from the database """
        if self._requester:
            data = self._requester.get(self._url)
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

    def get_supplier_parts(self):

        response = self._requester.get(
            SupplierPart.URL,
            params={
                'part': self['pk']
            })

        parts = []

        for part in response:
            if 'pk' in part.keys():
                parts.append(SupplierPart(data=part, requester=self._requester))

        return parts

    
class SupplierPart(InventreeObject):
    """ Class for maniuplating a SupplierPart object """

    URL = 'company/part'

    def get_price_breaks(self):

        response = self._requester.get(
            SupplierPriceBreak.URL,
            params={
                'part': self['pk']
            })

        breaks = []

        for brk in response:
            if 'pk' in brk.keys():
                breaks.append(SupplierPriceBreak(self._requester, data=brk))

        return breaks


class SupplierPriceBreak(InventreeObject):

    URL = 'company/price-break/'