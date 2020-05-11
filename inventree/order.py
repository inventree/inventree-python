# -*- coding: utf-8 -*-

from inventree import base


class PurchaseOrder(base.InventreeObject):
    """ Class representing the PurchaseOrder database model """

    URL = 'order/po'
    filters = [
        'status',
        'part',
        'supplier_part',
        'supplier',
    ]


class SalesOrder(base.InventreeObject):
    """ Class respresenting the SalesOrder database model """

    URL = 'order/so'
    filters = [
        'status',
        'part',
        'customer',
    ]
