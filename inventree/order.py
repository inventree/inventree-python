# -*- coding: utf-8 -*-

from inventree import base


class PurchaseOrder(base.InventreeObject):
    """ Class representing the PurchaseOrder database model """

    URL = 'order/po'
    FILTERS = [
        'status',
        'part',
        'supplier_part',
        'supplier',
    ]

    def __repr__(self):
        return "Purchase Order #{ref}".format(ref=self.pk)

    def getLineItems(self):
        """ Return the line items associated with this order """
        return PurchaseOrderLineItem.list(self._api, order=self.pk)


class PurchaseOrderLineItem(base.InventreeObject):
    """ Class representing the PurchaseOrderLineItem database model """

    URL = 'order/po-line/'
    FILTERS = [
        'order',
        'part',
    ]

    def __repr__(self):
        return "{n} x part #{part} for order #{ref}".format(
            n=self['quantity'],
            part=self['part'],
            ref=self['order']
        )


class SalesOrder(base.InventreeObject):
    """ Class respresenting the SalesOrder database model """

    URL = 'order/so'
    FILTERS = [
        'status',
        'part',
        'customer',
    ]

    def __repr__(self):
        return "Sales Order #{ref}".format(ref=self.pk)

    def getLineItems(self):
        """ Return the line items associated with this order """
        return SalesOrderLineItem.list(self._api, order=self.pk)


class SalesOrderLineItem(base.InventreeObject):
    """ Class representing the SalesOrderLineItem database model """

    URL = 'order/so-line/'
    FILTERS = [
        'order',
        'part'
    ]

    def __repr__(self):
        return "{n} x part #{part} for order #{ref}".format(
            n=self['quantity'],
            part=self['part'],
            ref=self['order']
        )
