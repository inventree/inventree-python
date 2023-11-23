# -*- coding: utf-8 -*-

import logging
import re

import inventree.base
import inventree.build
import inventree.company
import inventree.label
import inventree.report
import inventree.stock

logger = logging.getLogger('inventree')


class PartCategoryParameterTemplate(inventree.base.InventreeObject):
    """A model which link a ParameterTemplate to a PartCategory"""

    URL = 'part/category/parameters'

    def getCategory(self):
        """Return the referenced PartCategory instance"""
        return PartCategory(self._api, self.category)

    def getTemplate(self):
        """Return the referenced ParameterTemplate instance"""
        return ParameterTemplate(self._api, self.parameter_template)


class PartCategory(inventree.base.MetadataMixin, inventree.base.InventreeObject):
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

    def getCategoryParameterTemplates(self, fetch_parent: bool = True) -> list:
        """Fetch a list of default parameter templates associated with this category

        Arguments:
            fetch_parent: If True (default) include templates for parents also
        """

        return PartCategoryParameterTemplate.list(
            self._api,
            category=self.pk,
            fetch_parent=fetch_parent
        )


class Part(inventree.base.BarcodeMixin, inventree.base.MetadataMixin, inventree.base.ImageMixin, inventree.label.LabelPrintingMixin, inventree.base.InventreeObject):
    """ Class representing the Part database model """

    URL = 'part'

    # Setup for Label printing
    LABELNAME = 'part'
    LABELITEM = 'parts'

    def getCategory(self):
        """ Return the part category associated with this part """
        return PartCategory(self._api, self.category)

    def getTestTemplates(self):
        """ Return all test templates associated with this part """
        return PartTestTemplate.list(self._api, part=self.pk)

    def getSupplierParts(self):
        """ Return the supplier parts associated with this part """
        if self.purchaseable:
            return inventree.company.SupplierPart.list(self._api, part=self.pk)
        else:
            return list()

    def getManufacturerParts(self):
        """ Return the manufacturer parts associated with this part """
        return inventree.company.ManufacturerPart.list(self._api, part=self.pk)

    def getBomItems(self, **kwargs):
        """ Return the items required to make this part """
        return BomItem.list(self._api, part=self.pk, **kwargs)

    def isUsedIn(self):
        """ Return a list of all the parts this part is used in """
        return BomItem.list(self._api, sub_part=self.pk)

    def getBuilds(self, **kwargs):
        """ Return the builds associated with this part """
        return inventree.build.Build.list(self._api, part=self.pk, **kwargs)

    def getStockItems(self, **kwargs):
        """ Return the stock items associated with this part """
        return inventree.stock.StockItem.list(self._api, part=self.pk, **kwargs)

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

    def getRequirements(self):
        """
        Get required amounts from requirements API endpoint for this part
        """

        # Set the url
        URL = f"{self.URL}/{self.pk}/requirements/"

        # Get data
        return self._api.get(URL)


class PartAttachment(inventree.base.Attachment):
    """ Class representing a file attachment for a Part """

    URL = 'part/attachment'

    REQUIRED_KWARGS = ['part']


class PartTestTemplate(inventree.base.MetadataMixin, inventree.base.InventreeObject):
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


class BomItem(
    inventree.base.InventreeObject,
    inventree.base.MetadataMixin,
    inventree.report.ReportPrintingMixin,
):
    """ Class representing the BomItem database model """

    URL = 'bom'

    # Setup for Report mixin
    REPORTNAME = 'bom'
    REPORTITEM = 'part'


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

        if isinstance(part1, Part):
            pk_1 = part1.pk
        else:
            pk_1 = int(part1)
        if isinstance(part2, Part):
            pk_2 = part2.pk
        else:
            pk_2 = int(part2)

        data = {
            'part_1': pk_1,
            'part_2': pk_2,
        }

        # Send the data to the server
        return api.post(cls.URL, data)


class Parameter(inventree.base.InventreeObject):
    """class representing the Parameter database model """
    URL = 'part/parameter'

    def getunits(self):
        """ Get the units for this parameter """

        return self._data['template_detail']['units']


class ParameterTemplate(inventree.base.InventreeObject):
    """ class representing the Parameter Template database model"""

    URL = 'part/parameter/template'
