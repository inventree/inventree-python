# -*- coding: utf-8 -*-

import inventree.base
import inventree.part
import inventree.company


class PurchaseOrder(inventree.base.MetadataMixin, inventree.base.InventreeObject):
    """ Class representing the PurchaseOrder database model """

    URL = 'order/po'

    def getLineItems(self, **kwargs):
        """ Return the line items associated with this order """
        return PurchaseOrderLineItem.list(self._api, order=self.pk, **kwargs)

    def getExtraLineItems(self, **kwargs):
        """ Return the line items associated with this order """
        return PurchaseOrderExtraLineItem.list(self._api, order=self.pk, **kwargs)

    def addLineItem(self, **kwargs):
        """
        Create (and return) new PurchaseOrderLineItem object against this PurchaseOrder
        """

        kwargs['order'] = self.pk

        return PurchaseOrderLineItem.create(self._api, data=kwargs)

    def addExtraLineItem(self, **kwargs):
        """
        Create (and return) new PurchaseOrderExtraLineItem object against this PurchaseOrder
        """

        kwargs['order'] = self.pk

        return PurchaseOrderExtraLineItem.create(self._api, data=kwargs)

    def getAttachments(self):
        return PurchaseOrderAttachment.list(self._api, order=self.pk)
    
    def uploadAttachment(self, attachment, comment=''):
        return PurchaseOrderAttachment.upload(
            self._api,
            attachment,
            comment=comment,
            order=self.pk,
        )


class PurchaseOrderLineItem(inventree.base.InventreeObject):
    """ Class representing the PurchaseOrderLineItem database model """

    URL = 'order/po-line'

    def getSupplierPart(self):
        """
        Return the SupplierPart associated with this PurchaseOrderLineItem
        """
        return inventree.company.SupplierPart(self._api, self.part)

    def getPart(self):
        """
        Return the Part referenced by the associated SupplierPart
        """
        return inventree.part.Part(self._api, self.getSupplierPart().part)

    def getOrder(self):
        """
        Return the PurchaseOrder to which this PurchaseOrderLineItem belongs
        """
        return PurchaseOrder(self._api, self.order)


class PurchaseOrderExtraLineItem(inventree.base.InventreeObject):
    """ Class representing the PurchaseOrderExtraLineItem database model """

    URL = 'order/po-extra-line'

    def getOrder(self):
        """
        Return the PurchaseOrder to which this PurchaseOrderLineItem belongs
        """
        return PurchaseOrder(self._api, self.order)


class PurchaseOrderAttachment(inventree.base.Attachment):
    """Class representing a file attachment for a PurchaseOrder"""

    URL = 'order/po/attachment'

    REQUIRED_KWARGS = ['order']


class SalesOrder(inventree.base.MetadataMixin, inventree.base.InventreeObject):
    """ Class respresenting the SalesOrder database model """

    URL = 'order/so'

    def getLineItems(self, **kwargs):
        """ Return the line items associated with this order """
        return SalesOrderLineItem.list(self._api, order=self.pk, **kwargs)

    def getExtraLineItems(self, **kwargs):
        """ Return the line items associated with this order """
        return SalesOrderExtraLineItem.list(self._api, order=self.pk, **kwargs)

    def addLineItem(self, **kwargs):
        """
        Create (and return) new SalesOrderLineItem object against this SalesOrder
        """

        kwargs['order'] = self.pk

        return SalesOrderLineItem.create(self._api, data=kwargs)

    def addExtraLineItem(self, **kwargs):
        """
        Create (and return) new SalesOrderExtraLineItem object against this SalesOrder
        """

        kwargs['order'] = self.pk

        return SalesOrderExtraLineItem.create(self._api, data=kwargs)

    def getAttachments(self):
        return SalesOrderAttachment.list(self._api, order=self.pk)
    
    def uploadAttachment(self, attachment, comment=''):
        return SalesOrderAttachment.upload(
            self._api,
            attachment,
            comment=comment,
            order=self.pk,
        )
    
    def getShipments(self, **kwargs):
        """ Return the shipments associated with this order """
        
        return SalesOrderShipment.list(self._api, order=self.pk, **kwargs)

    def addShipment(self, reference, **kwargs):
        """ Create (and return) new SalesOrderShipment
        against this SalesOrder """

        kwargs['order'] = self.pk
        kwargs['reference'] = reference

        return SalesOrderShipment.create(self._api, data=kwargs)


class SalesOrderLineItem(inventree.base.InventreeObject):
    """ Class representing the SalesOrderLineItem database model """

    URL = 'order/so-line'

    def getPart(self):
        """
        Return the Part object referenced by this SalesOrderLineItem
        """
        return inventree.part.Part(self._api, self.part)

    def getOrder(self):
        """
        Return the SalesOrder to which this SalesOrderLineItem belongs
        """
        return SalesOrder(self._api, self.order)


class SalesOrderExtraLineItem(inventree.base.InventreeObject):
    """ Class representing the SalesOrderExtraLineItem database model """

    URL = 'order/so-extra-line'

    def getOrder(self):
        """
        Return the SalesOrder to which this SalesOrderLineItem belongs
        """
        return SalesOrder(self._api, self.order)


class SalesOrderAttachment(inventree.base.Attachment):
    """Class representing a file attachment for a SalesOrder"""

    URL = 'order/so/attachment'

    REQUIRED_KWARGS = ['order']


class SalesOrderShipment(inventree.base.InventreeObject):
    """Class representing a shipment for a SalesOrder"""

    URL = 'order/so/shipment'

    def getOrder(self):
        """
        Return the SalesOrder to which this SalesOrderShipment belongs
        """
        return SalesOrder(self._api, self.order)
    
    def allocateItems(self, items=[]):
        """
        Function to allocate items to the current shipment
        
        items is expected to be a list containing dicts, one for each item
        to be assigned. Each dict should contain three parameters, as
        follows:
            items = [{
                "line_item": 25,
                "quantity": 150,
                "stock_item": 26
            }
        """

        # Customise URL
        url = f'order/so/{self.getOrder().pk}/allocate'

        # Create data from given inputs
        data = {
            'items': items,
            'shipment': self.pk
        }

        return self._api.post(url, data)