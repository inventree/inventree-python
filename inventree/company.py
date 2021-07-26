# -*- coding: utf-8 -*-

import os
import logging

import inventree.base
import inventree.order


logger = logging.getLogger('inventree')


class Company(inventree.base.InventreeObject):
    """ Class representing the Company database model """

    URL = 'company'

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
        return inventree.order.PurchaseOrder.list(self._api, supplier=self.pk)

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
        return inventree.order.SalesOrder.list(self._api, customer=self.pk)

    def createSalesOrder(self, **kwargs):
        """
        Create (and return) a new SalesOrder against this company
        """

        kwargs['customer'] = self.pk

        return inventree.order.SalesOrder.create(
            self._api,
            data=kwargs
        )

    def uploadImage(self, image):
        """
        Upload an image file against this Company
        
        Returns the HTTP response object
        """

        files = {}

        if image:
            if os.path.exists(image):
                f = os.path.basename(image)
                fo = open(image, 'rb')
                files['image'] = (f, fo)
            else:
                logger.error(f"Image '{image}' does not exist")
                return None

        response = self.save(
            data={},
            files=files,
        )

        return response

    def downloadImage(self, destination):
        """
        Download the image for this Company, to the specified destination
        """

        if self.image:
            return self._api.downloadFile(self.image, destination)
        else:
            logger.error(f"Company '{self.name}' does not have an associated image")
            return False


class SupplierPart(inventree.base.InventreeObject):
    """ Class representing the SupplierPart database model """

    URL = 'company/part'

    def getPriceBreaks(self):
        """ Get a list of price break objects for this SupplierPart """

        return SupplierPriceBreak.list(self._api, part=self.pk)


class ManufacturerPart(inventree.base.InventreeObject):
    """
    Class representing the ManufacturerPart database model
    """

    URL = 'company/part/manufacturer'

    def getParameters(self, **kwargs):
        """
        GET a list of all ManufacturerPartParameter objects for this ManufacturerPart
        """

        return ManufacturerPartParameter.list(self._api, manufacturer_part=self.pk, **kwargs)


class ManufacturerPartParameter(inventree.base.InventreeObject):
    """
    Class representing the ManufacturerPartParameter database model.
    """

    URL = 'company/part/manufacturer/parameter'


class SupplierPriceBreak(inventree.base.InventreeObject):
    """ Class representing the SupplierPriceBreak database model """

    URL = 'company/price-break'
