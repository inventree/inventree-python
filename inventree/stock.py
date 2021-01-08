# -*- coding: utf-8 -*-

import os
import logging

import inventree.base
import inventree.part


class StockLocation(inventree.base.InventreeObject):
    """ Class representing the StockLocation database model """

    URL = 'stock/location'

    def getStockItems(self, **kwargs):
        return StockItem.list(self._api, location=self.pk, **kwargs)

    def getParentLocation(self):
        """
        Return the parent stock location
        (or None if no parent is available)
        """

        if self.parent is None:
            return None
        
        return StockLocation(self._api, pk=self.parent)

    def getChildLocations(self, **kwargs):
        """
        Return all the child locations under this location
        """
        return StockLocation.list(self._api, parent=self.pk, **kwargs)


class StockItem(inventree.base.InventreeObject):
    """ Class representing the StockItem database model.
    
    Stock items can be filtered by:
    
    - location: Where the stock item is stored
    - category: The category of the part this stock item points to
    - supplier: Who supplied this stock item
    - part: The part referenced by this stock item
    - supplier_part: Matching SupplierPart object
    """

    URL = 'stock'

    def getPart(self):
        """ Return the base Part object associated with this StockItem """
        return inventree.part.Part(self._api, self.part)

    def getLocation(self):
        """
        Return the StockLocation associated with this StockItem
        
        Returns None if there is no linked StockItem
        """

        if self.location is None:
            return None

        return StockLocation(self._api, self.location)

    def getAttachments(self):
        """ Return all file attachments for this StockItem """

        return StockItemAttachment.list(
            self._api,
            stock_item=self.pk
        )

    def uploadAttachment(self, filename, comment, **kwargs):
        """ Upload a file attachment against this StockItem """

        kwargs['stock_item'] = self.pk

        StockItemAttachment.upload(self._api, filename, comment, **kwargs)

    def getTestResults(self, **kwargs):
        """ Return all the test results associated with this StockItem """

        return StockItemTestResult.list(self._api, stock_item=self.pk)

    def uploadTestResult(self, test_name, test_result, **kwargs):
        """ Upload a test result against this StockItem """

        return StockItemTestResult.upload_result(self._api, self.pk, test_name, test_result, **kwargs)


class StockItemAttachment(inventree.base.Attachment):
    """ Class representing a file attachment for a StockItem """

    URL = 'stock/attachment'


class StockItemTracking(inventree.base.InventreeObject):
    """ Class representing a StockItem tracking object """

    URL = 'stock/track'


class StockItemTestResult(inventree.base.InventreeObject):
    """ Class representing a StockItemTestResult object """

    URL = 'stock/test'

    def getTestKey(self):
        return inventree.part.PartTestTemplate.generateTestKey(self.test)

    @classmethod
    def upload_result(cls, api, stock_item, test, result, **kwargs):
        """
        Upload a test result.

        args:
            api: Authenticated InvenTree API object
            stock_item: pk of the StockItem object to upload the test result against
            test: Name of the test (string)
            result: Test result (boolean)

        kwargs:
            attachment: Optionally attach a file to the test result
            notes: Add extra notes
            value: Add a "value" to the test (e.g. an actual measurement made during the test)
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
                logging.error("File does not exist: '{f}'".format(f=attachment))

        notes = kwargs.get('notes', '')
        value = kwargs.get('value', '')

        data = {
            'stock_item': stock_item,
            'test': test,
            'result': result,
            'notes': notes,
            'value': value,
        }

        # Send the data to the serever
        if api.post(cls.URL, data, files=files):
            logging.info("Uploaded test result: '{test}'".format(test=test))
            ret = True
        else:
            logging.warning("Test upload failed")
            ret = False

        # Ensure the file attachment is closed after use
        if fo:
            fo.close()

        return ret
