# -*- coding: utf-8 -*-

from inventree import base


class Company(base.InventreeObject):
    """ Class representing the Company database model """

    URL = 'company'
    FILTERS = ['is_supplier', 'is_customer']

    def get_supplier_parts(self):
        return SupplierPart.list(self._api, part=self.pk)


class SupplierPart(base.InventreeObject):
    """ Class representing the SupplierPart database model """

    URL = 'company/part'
    FILTERS = ['part', 'supplier']

    def get_price_breaks(self):
        """ Get a list of price break objects for this SupplierPart """

        return SupplierPriceBreak.list(self._api, part=self.pk)


class SupplierPriceBreak(base.InventreeObject):
    """ Class representing the SupplierPriceBreak database model """

    URL = 'company/price-break/'
    FILTERS = ['part', 'currency']
