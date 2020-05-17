# -*- coding: utf-8 -*-

import re

from inventree import base
from inventree import stock
from inventree import company
from inventree import build


class PartCategory(base.InventreeObject):
    """ Class representing the PartCategory database model """

    URL = 'part/category'
    FILTERS = ['parent']

    def getParts(self):
        return Part.list(self._api, category=self.pk)

    def getChildCategories(self):
        return PartCategory.list(self._api, parent=self.pk)
    

class Part(base.InventreeObject):
    """ Class representing the Part database model """

    URL = 'part'
    FILTERS = [
        'category',
        'cascade',
        'has_stock',
        'low_stock',
        'is_template',
        'variant_of',
        'assemply',
        'component',
        'trackable',
        'salable',
        'active',
        'buildable',
        'purchaseable',
    ]

    def getTestTemplates(self):
        """ Return all test templates associated with this part """
        return PartTestTemplate.list(self._api, part=self.pk)

    def getSupplierParts(self):
        """ Return the supplier parts associated with this part """
        return company.SupplierPart.list(self._api, part=self.pk)

    def getBomItems(self):
        """ Return the items required to make this part """
        return BomItem.list(self._api, part=self.pk)

    def isUsedIn(self):
        """ Return a list of all the parts this part is used in """
        return BomItem.list(self._api, sub_part=self.pk)

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


class PartTestTemplate(base.InventreeObject):
    """ Class representing a test template for a Part """

    URL = 'part/test-template'
    FILTERS = ['part', 'required']

    @classmethod
    def generateTestKey(cls, test_name):
        """ Generate a 'key' for this test """

        key = test_name.strip().lower()
        key = key.replace(' ', '')

        # Remove any characters that cannot be used to represent a variable
        key = re.sub(r'[^a-zA-Z0-9]', '', key)

        return key

    def getTestKey(self):
        return PartTestTemplate.generateTestKey(self.test_name)
    

class BomItem(base.InventreeObject):
    """ Class representing the BomItem database model """

    URL = 'bom'
    FILTERS = ['part', 'sub_part']
