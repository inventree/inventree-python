# -*- coding: utf-8 -*-

import logging

import inventree.base
import inventree.order

logger = logging.getLogger('inventree')


class Contact(inventree.base.InventreeObject):
    """Class representing the Contact model"""

    URL = 'company/contact/'
    REQUIRED_API_VERSION = 104


class Company(inventree.base.ImageMixin, inventree.base.MetadataMixin, inventree.base.InventreeObject):
    """ Class representing the Company database model """

    URL = 'company'

    def getContacts(self, **kwargs):
        """Return contacts associated with this Company"""
        kwargs['company'] = self.pk
        return Contact.list(self._api, **kwargs)

    def getSuppliedParts(self, **kwargs):
        """
        Return list of SupplierPart objects supplied by this Company
        """
        return SupplierPart.list(self._api, supplier=self.pk, **kwargs)

    def getManufacturedParts(self, **kwargs):
        """
        Return list of ManufacturerPart objects manufactured by this Company
        """
        return ManufacturerPart.list(self._api, manufacturer=self.pk, **kwargs)

    def getPurchaseOrders(self, **kwargs):
        """
        Return list of PurchaseOrder objects associated with this company
        """
        return inventree.order.PurchaseOrder.list(self._api, supplier=self.pk, **kwargs)

    def createPurchaseOrder(self, **kwargs):
        """
        Create (and return) a new PurchaseOrder against this company
        """

        kwargs['supplier'] = self.pk

        return inventree.order.PurchaseOrder.create(
            self._api,
            data=kwargs
        )

    def getSalesOrders(self, **kwargs):
        """
        Return list of SalesOrder objects associated with this company
        """
        return inventree.order.SalesOrder.list(self._api, customer=self.pk, **kwargs)

    def createSalesOrder(self, **kwargs):
        """
        Create (and return) a new SalesOrder against this company
        """

        kwargs['customer'] = self.pk

        return inventree.order.SalesOrder.create(
            self._api,
            data=kwargs
        )

    def getReturnOrders(self, **kwargs):
        """Return list of ReturnOrder objects associated with this company"""
        return inventree.order.ReturnOrder.list(self._api, customer=self.pk, **kwargs)

    def createReturnOrder(self, **kwargs):
        """Create (and return) a new ReturnOrder against this company"""
        kwargs['customer'] = self.pk

        return inventree.order.ReturnOrder.create(self._api, data=kwargs)


class SupplierPart(inventree.base.BarcodeMixin, inventree.base.BulkDeleteMixin, inventree.base.MetadataMixin, inventree.base.InventreeObject):
    """Class representing the SupplierPart database model

    - Implements the BulkDeleteMixin
    """

    URL = 'company/part'

    def getPriceBreaks(self):
        """ Get a list of price break objects for this SupplierPart """

        return SupplierPriceBreak.list(self._api, part=self.pk)


class ManufacturerPart(inventree.base.BulkDeleteMixin, inventree.base.MetadataMixin, inventree.base.InventreeObject):
    """Class representing the ManufacturerPart database model

    - Implements the BulkDeleteMixin
    """

    URL = 'company/part/manufacturer'

    def getParameters(self, **kwargs):
        """
        GET a list of all ManufacturerPartParameter objects for this ManufacturerPart
        """

        return ManufacturerPartParameter.list(self._api, manufacturer_part=self.pk, **kwargs)

    def getAttachments(self, **kwargs):

        return ManufacturerPartAttachment.list(self._api, manufacturer_part=self.pk, **kwargs)

    def uploadAttachment(self, attachment, comment=''):

        return ManufacturerPartAttachment.upload(
            self._api,
            attachment,
            comment=comment,
            manufacturer_part=self.pk,
        )


class ManufacturerPartParameter(inventree.base.BulkDeleteMixin, inventree.base.InventreeObject):
    """Class representing the ManufacturerPartParameter database model.

    - Implements the BulkDeleteMixin
    """

    URL = 'company/part/manufacturer/parameter'


class ManufacturerPartAttachment(inventree.base.Attachment):
    """
    Class representing the ManufacturerPartAttachment model
    """

    URL = 'company/part/manufacturer/attachment'


class SupplierPriceBreak(inventree.base.InventreeObject):
    """ Class representing the SupplierPriceBreak database model """

    URL = 'company/price-break'
