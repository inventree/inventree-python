# -*- coding: utf-8 -*-

import inventree.base


class Company(inventree.base.InventreeObject):
    """ Class representing the Company database model """

    URL = 'company'

    def getSuppliedParts(self):
        return SupplierPart.list(self._api, supplier=self.pk)

    def getManufacturedParts(self):
        return ManufacturerPart.list(self._api, manufacturer=self.pk)


class SupplierPart(inventree.base.InventreeObject):
    """ Class representing the SupplierPart database model """

    URL = 'company/part'

    def getPriceBreaks(self):
        """ Get a list of price break objects for this SupplierPart """

        return SupplierPriceBreak.list(self._api, part=self.pk)


class ManufacturerPart(inventree.base.InventreeObject):
    """ Class representing the ManufacturerPart database model """

    URL = 'company/part/manufacturer'


class SupplierPriceBreak(inventree.base.InventreeObject):
    """ Class representing the SupplierPriceBreak database model """

    URL = 'company/price-break/'
