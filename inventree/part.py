# -*- coding: utf-8 -*-

import logging
import re

import inventree.base
import inventree.stock
import inventree.company
import inventree.build


logger = logging.getLogger('inventree')


class PartCategory(inventree.base.InventreeObject):
    """ Class representing the PartCategory database model """

    URL = 'part/category'

    def getParts(self, **kwargs):
        return Part.list(self._api, category=self.pk, **kwargs)

    def getParentCategory(self):
        if self.parent:
            return PartCategory(self._api, self.parent)
        else:
            return None

    def getChildCategories(self, **kwargs):
        return PartCategory.list(self._api, parent=self.pk, **kwargs)

    def get_category_parameter_templates(self, fetch_parent=True):
        """
            fetch_parent: enable to fetch templates for parent categories
        """

        parameters_url = f'part/category/{self.pk}/parameters'

        return self.list(self._api,
                         url=parameters_url,
                         fetch_parent=fetch_parent)


class Part(inventree.base.ImageMixin, inventree.base.InventreeObject):
    """ Class representing the Part database model """

    URL = 'part'

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

    def getBuilds(self, **kwargs):
        """ Return the builds associated with this part """
        return inventree.build.Build.list(self._api, part=self.pk, **kwargs)

    def getStockItems(self):
        """ Return the stock items associated with this part """
        return inventree.stock.StockItem.list(self._api, part=self.pk)

    def getParameters(self):
        """ Return parameters associated with this part """
        return Parameter.list(self._api, part=self.pk)

    def getRelated(self):
        """ Return related parts associated with this part """
        return PartRelated.list(self._api, part=self.pk)

    def getInternalPriceList(self):
        """
        Returns the InternalPrice list for this part
        """

        return InternalPrice.list(self._api, part=self.pk)
    
    def setInternalPrice(self, quantity: int, price: float):
        """
        Set the internal price for this part
        """

        return InternalPrice.setInternalPrice(self._api, self.pk, quantity, price)

    def getAttachments(self):
        return PartAttachment.list(self._api, part=self.pk)

    def uploadAttachment(self, attachment, comment=''):
        """
        Upload an attachment (file) against this Part.

        Args:
            attachment: Either a string (filename) or a file object
            comment: Attachment comment
        """

        return PartAttachment.upload(
            self._api,
            attachment,
            comment=comment,
            part=self.pk
        )


class PartAttachment(inventree.base.Attachment):
    """ Class representing a file attachment for a Part """

    URL = 'part/attachment'

    REQUIRED_KWARGS = ['part']


class PartTestTemplate(inventree.base.InventreeObject):
    """ Class representing a test template for a Part """

    URL = 'part/test-template'

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


class InternalPrice(inventree.base.InventreeObject):
    """ Class representing the InternalPrice model """

    URL = 'part/internal-price'

    @classmethod
    def setInternalPrice(cls, api, part, quantity: int, price: float):
        """
        Set the internal price for this part
        """

        data = {
            'part': part,
            'quantity': quantity,
            'price': price,
        }

        # Send the data to the server
        return api.post(cls.URL, data)
    
    
class PartRelated(inventree.base.InventreeObject):
    """ Class representing a relationship between parts"""

    URL = 'part/related'

    @classmethod
    def add_related(cls, api, part1, part2):
    
        data = {
            'part_1': part1,
            'part_2': part2,
        }
        # Send the data to the server
        if api.post(cls.URL, data):
            logging.info("Related OK")
            ret = True
        else:
            logging.warning("Related failed")
            ret = False
        return ret


class Parameter(inventree.base.InventreeObject):
    """class representing the Parameter database model """
    URL = 'part/parameter'

    def getunits(self):
        """ Get the dimension and units for this parameter """

        return [element for element
                in ParameterTemplate.list(self._api)
                if element['pk'] == self._data['template']]


class ParameterTemplate(inventree.base.InventreeObject):
    """ class representing the Parameter Template database model"""

    URL = 'part/parameter/template'
