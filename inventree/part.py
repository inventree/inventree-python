# -*- coding: utf-8 -*-


from inventree import base
from inventree import stock
from inventree import company
from inventree import build


class PartCategory(base.InventreeObject):
    """ Class representing the PartCategory database model """

    URL = 'part/category'
    FILTERS = ['parent']

    def get_parts(self):
        return Part.list(self._api, category=self.pk)
    

class Part(base.InventreeObject):
    """ Class representing the Part database model """

    URL = 'part'
    FILTERS = ['category', 'buildable', 'purchaseable']

    def getSupplierParts(self):
        """ Return the supplier parts associated with this part """
        return company.SupplierPart.list(self._api, part=self.pk)

    def getBomItems(self):
        """ Return the items required to make this part """
        return BomItem.list(self._api, part=self.pk)

    def getBuilds(self):
        """ Return the builds associated with this part """
        return build.Build.list(self._api, part=self.pk)

    def getStockItems(self):
        """ Return the stock items associated with this part """
        return stock.StockItem.list(self._api, part=self.pk)

    def getAttachments(self):
        """ Return attachments associated with this part """
        return PartAttachment.list(self._api, part=self.pk)


class PartAttachment(base.Attachment):
    """ Class representing a file attachment for a Part """

    URL = 'part/attachment'
    FILTERS = ['part']
    

class BomItem(base.InventreeObject):
    """ Class representing the BomItem database model """

    URL = 'bom'
    FILTERS = ['part', 'sub_part']
