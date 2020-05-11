# -*- coding: utf-8 -*-

from inventree import base


class StockLocation(base.InventreeObject):
    """ Class representing the StockLocation database model """

    URL = 'stock/location'
    filters = ['parent']

    def get_stock_items(self):
        return StockItem.list(self._api, location=self.pk)


class StockItem(base.InventreeObject):
    """ Class representing the StockItem database model.
    
    Stock items can be filtered by:
    
    - location: Where the stock item is stored
    - category: The category of the part this stock item points to
    - supplier: Who supplied this stock item
    - part: The part referenced by this stock item
    - supplier_part: Matching SupplierPart object
    """

    URL = 'stock'
    FILTERS = ['location', 'category', 'supplier', 'part', 'supplier_part']


class StocKItemAttachment(base.Attachment):
    """ Class representing a file attachment for a StockItem """

    URL = 'stock/attachment'
    FILTERS = ['stock_item']
