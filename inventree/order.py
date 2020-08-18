# -*- coding: utf-8 -*-

import inventree.base
import inventree.part


class PurchaseOrder(inventree.base.InventreeObject):
    """ Class representing the PurchaseOrder database model """

    URL = 'order/po'

    def __repr__(self):
        return "Purchase Order #{ref}".format(ref=self.pk)

    def getLineItems(self):
        """ Return the line items associated with this order """
        return PurchaseOrderLineItem.list(self._api, order=self.pk)


class PurchaseOrderLineItem(inventree.base.InventreeObject):
    """ Class representing the PurchaseOrderLineItem database model """

    URL = 'order/po-line/'

    def __repr__(self):
        return "{n} x part #{part} for order #{ref}".format(
            n=self.quantity,
            part=self.part,
            ref=self.order
        )

    def getPart(self):
        return inventree.part.Part(self._api, self.part)

    def getOrder(self):
        return PurchaseOrder(self._api, self.order)


class SalesOrder(inventree.base.InventreeObject):
    """ Class respresenting the SalesOrder database model """

    URL = 'order/so'

    def __repr__(self):
        return "Sales Order #{ref}".format(ref=self.pk)

    def getLineItems(self):
        """ Return the line items associated with this order """
        return SalesOrderLineItem.list(self._api, order=self.pk)


class SalesOrderLineItem(inventree.base.InventreeObject):
    """ Class representing the SalesOrderLineItem database model """

    URL = 'order/so-line/'

    def __repr__(self):
        return "{n} x part #{part} for order #{ref}".format(
            n=self.quantity,
            part=self.part,
            ref=self.order,
        )

    def getPart(self):
        return inventree.part.Part(self._api, self.part)

    def getOrder(self):
        return SalesOrder(self._api, self.order)
