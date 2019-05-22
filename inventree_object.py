import json


class InventreeObject():
    """ Base class for an InvenTree object """

    def __init__(self, url, requester, raw_data={}):
        """ Insantiate this InvenTree object.

        Args:
            url - The URL associated with this object on the server
            requester - The request manager object
            data - JSON representation of the object
        """

        self._url = url
        self._requester = requester
        self._data = raw_data

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