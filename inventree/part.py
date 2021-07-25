# -*- coding: utf-8 -*-

import os
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


class Part(inventree.base.InventreeObject):
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

    def getAttachments(self):
        """ Return attachments associated with this part """
        return PartAttachment.list(self._api, part=self.pk)

    def getParameters(self):
        """ Return parameters associated with this part """
        return inventree.base.Parameter.list(self._api, part=self.pk)

    def uploadImage(self, image):
        """
        Upload an image against this Part

        args:
            - image: path to an image file
        
        Returns the HTTP response object
        """

        files = {}

        if image:
            if os.path.exists(image):
                f = os.path.basename(image)
                fo = open(image, 'rb')
                files['image'] = (f, fo)
            else:
                logger.error("File does not exist: '{f}'".format(f=image))
                return None

        response = self.save(
            data={},
            files=files
        )

        return response

    def downloadImage(self, destination):
        """
        Download the image for this Part, to the specified destination
        """

        if self.image:
            return self._api.downloadFile(self.image, destination)
        else:
            logger.error(f"Part '{self.name}' does not have an associated image")
            return False


class PartAttachment(inventree.base.Attachment):
    """ Class representing a file attachment for a Part """

    URL = 'part/attachment'

    @classmethod
    def upload_attachment(cls, api, part, **kwargs):
        """
        Upload a Part attachment

        args:
            api: Authenticated InvenTree API object
            part: pk of the Part object to upload the attachment to

        kwargs:
            attachment: Attach a file
            comment: Add comment
        """
        attachment = kwargs.get('attachment', None)

        files = {}

        fo = None

        if attachment:
            if os.path.exists(attachment):
                f = os.path.basename(attachment)
                fo = open(attachment, 'rb')
                files['attachment'] = (f, fo)
            else:
                logger.error("File does not exist: '{f}'".format(f=attachment))

        comment = kwargs.get('comment', '')

        data = {
            'part': part,
            'attachment': os.path.basename(attachment),
            'comment': comment,
        }

        # Send the data to the server
        if api.post(cls.URL, data, files=files):
            logger.info("Uploaded attachment: '{f}'".format(f=attachment))
            ret = True
        else:
            logger.warning("Attachment upload failed")
            ret = False

        return ret


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
