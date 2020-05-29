# -*- coding: utf-8 -*-

import re

import inventree.base
import inventree.stock
import inventree.company
import inventree.build


class PartCategory(inventree.base.InventreeObject):
    """ Class representing the PartCategory database model """

    URL = 'part/category'
    FILTERS = ['parent']

    def getParts(self):
        return Part.list(self._api, category=self.pk)

    def getParentCategory(self):
        if self.parent:
            return PartCategory(self._api, self.parent)
        else:
            return None

    def getChildCategories(self):
        return PartCategory.list(self._api, parent=self.pk)
    

class Part(inventree.base.InventreeObject):
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

    def getCategory(self):
        """ Return the part category associated with this part """
        return PartCategory(self._api, self.category)

    def getTestTemplates(self):
        """ Return all test templates associated with this part """
        return PartTestTemplate.list(self._api, part=self.pk)

    def getSupplierParts(self):
        """ Return the supplier parts associated with this part """
        return inventree.company.SupplierPart.list(self._api, part=self.pk)

    def getBomItems(self):
        """ Return the items required to make this part """
        return BomItem.list(self._api, part=self.pk)

    def isUsedIn(self):
        """ Return a list of all the parts this part is used in """
        return BomItem.list(self._api, sub_part=self.pk)

    def getBuilds(self):
        """ Return the builds associated with this part """
        return inventree.build.Build.list(self._api, part=self.pk)

    def getStockItems(self):
        """ Return the stock items associated with this part """
        return inventree.stock.StockItem.list(self._api, part=self.pk)

    def getAttachments(self):
        """ Return attachments associated with this part """
        return PartAttachment.list(self._api, part=self.pk)


class PartAttachment(inventree.base.Attachment):
    """ Class representing a file attachment for a Part """

    URL = 'part/attachment'
    FILTERS = ['part']


class PartTestTemplate(inventree.base.InventreeObject):
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
    

class BomItem(inventree.base.InventreeObject):
    """ Class representing the BomItem database model """

    URL = 'bom'
    FILTERS = ['part', 'sub_part']
