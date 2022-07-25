# -*- coding: utf-8 -*-

import os
import logging

import inventree.api
import inventree.base
import inventree.part


class StockLocation(inventree.base.MetadataMixin, inventree.base.InventreeObject):
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


class StockItem(inventree.base.MetadataMixin, inventree.base.InventreeObject):
    """ Class representing the StockItem database model.
    
    Stock items can be filtered by:
    
    - location: Where the stock item is stored
    - category: The category of the part this stock item points to
    - supplier: Who supplied this stock item
    - part: The part referenced by this stock item
    - supplier_part: Matching SupplierPart object
    """

    URL = 'stock'

    @classmethod
    def adjustStock(cls, api: inventree.api.InvenTreeAPI, method: str, items: list, **kwargs):
        """Perform a generic stock 'adjustment' action.
        
        Arguments:
            api: InvenTreeAPI instance
            method: Adjument method, e.g. 'count' / 'add'
            items: List of items to include in the adjustment (see below)
            kwargs: Additional kwargs to send with the adjustment
        
        Items:
            Each 'item' in the 'items' list must be a dict object, containing the following fields:

            item: The 'pk' (primary key) identifier for a StockItem instance
            quantity: The quantity 
        """

        if method not in ['count', 'add', 'remove', 'transfer']:
            raise ValueError(f"Stock adjustment method '{method}' not supported")
        
        url = f"stock/{method}/"

        data = kwargs
        data['items'] = items

        return api.post(url, data=data)
    
    @classmethod
    def countStock(cls, api: inventree.api.InvenTreeAPI, items: list, **kwargs):
        """Perform 'count' adjustment for multiple stock items"""

        return cls.adjustStock(
            api,
            'count',
            items,
            **kwargs
        )

    @classmethod
    def addStock(cls, api: inventree.api.InvenTreeAPI, items: list, **kwargs):
        """Perform 'add' adjustment for multiple stock items"""

        return cls.adjustStock(
            api,
            'add',
            items,
            **kwargs
        )

    @classmethod
    def removeStock(cls, api: inventree.api.InvenTreeAPI, items: list, **kwargs):
        """Perform 'remove' adjustment for multiple stock items"""

        return cls.adjustStock(
            api,
            'remove',
            items,
            **kwargs
        )

    @classmethod
    def transferStock(cls, api: inventree.api.InvenTreeAPI, items: list, location: int, **kwargs):
        """Perform 'transfer' adjustment for multiple stock items"""

        kwargs['location'] = location

        return cls.adjustStock(
            api,
            'transfer',
            items,
            **kwargs
        )

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

    def getTestResults(self, **kwargs):
        """ Return all the test results associated with this StockItem """

        return StockItemTestResult.list(self._api, stock_item=self.pk)

    def uploadTestResult(self, test_name, test_result, **kwargs):
        """ Upload a test result against this StockItem """

        return StockItemTestResult.upload_result(self._api, self.pk, test_name, test_result, **kwargs)

    def getAttachments(self):
        """ Return all file attachments for this StockItem """

        return StockItemAttachment.list(
            self._api,
            stock_item=self.pk
        )

    def uploadAttachment(self, attachment, comment=''):
        """
        Upload an attachment against this StockItem
        """

        return StockItemAttachment.upload(
            self._api,
            attachment,
            comment=comment,
            stock_item=self.pk
        )


class StockItemAttachment(inventree.base.Attachment):
    """ Class representing a file attachment for a StockItem """

    URL = 'stock/attachment'

    REQUIRED_KWARGS = ['stock_item']


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
                logging.error(f"File does not exist: '{attachment}'")

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
            logging.info(f"Uploaded test result: '{test}'")
            ret = True
        else:
            logging.warning("Test upload failed")
            ret = False

        # Ensure the file attachment is closed after use
        if fo:
            fo.close()

        return ret
