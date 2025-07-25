# -*- coding: utf-8 -*-

import logging
import os

import inventree.api
import inventree.base
import inventree.company
import inventree.label
import inventree.part
import inventree.report


class StockLocation(
    inventree.base.BarcodeMixin,
    inventree.base.MetadataMixin,
    inventree.label.LabelPrintingMixin,
    inventree.report.ReportPrintingMixin,
    inventree.base.InventreeObject,
):
    """ Class representing the StockLocation database model """

    URL = 'stock/location'
    MODEL_TYPE = 'stocklocation'

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


class StockItem(
    inventree.base.AttachmentMixin,
    inventree.base.BarcodeMixin,
    inventree.base.BulkDeleteMixin,
    inventree.base.MetadataMixin,
    inventree.label.LabelPrintingMixin,
    inventree.base.InventreeObject,
):
    """Class representing the StockItem database model."""

    URL = 'stock'

    MODEL_TYPE = 'stockitem'

    @classmethod
    def adjustStockItems(cls, api: inventree.api.InvenTreeAPI, method: str, items: list, **kwargs):
        """Perform a generic stock 'adjustment' action.

        Arguments:
            api: InvenTreeAPI instance
            method: Adjument method, e.g. 'count' / 'add'
            items: List of items to include in the adjustment (see below)
            kwargs: Additional kwargs to send with the adjustment

        Items:
            Each 'item' in the 'items' list must be a dict object, containing the following fields:

            pk: The 'pk' (primary key) identifier for a StockItem instance
            quantity: The quantity of each stock item for the particular action
        """

        if method not in ['count', 'add', 'remove', 'transfer', 'assign']:
            raise ValueError(f"Stock adjustment method '{method}' not supported")

        url = f"stock/{method}/"

        data = kwargs
        data['items'] = items

        return api.post(url, data=data)

    @classmethod
    def countStockItems(cls, api: inventree.api.InvenTreeAPI, items: list, **kwargs):
        """Perform 'count' adjustment for multiple stock items"""

        return cls.adjustStockItems(
            api,
            'count',
            items,
            **kwargs
        )

    @classmethod
    def addStockItems(cls, api: inventree.api.InvenTreeAPI, items: list, **kwargs):
        """Perform 'add' adjustment for multiple stock items"""

        return cls.adjustStockItems(
            api,
            'add',
            items,
            **kwargs
        )

    @classmethod
    def removeStockItems(cls, api: inventree.api.InvenTreeAPI, items: list, **kwargs):
        """Perform 'remove' adjustment for multiple stock items"""

        return cls.adjustStockItems(
            api,
            'remove',
            items,
            **kwargs
        )

    @classmethod
    def transferStockItems(cls, api: inventree.api.InvenTreeAPI, items: list, location: int, **kwargs):
        """Perform 'transfer' adjustment for multiple stock items"""

        kwargs['location'] = location

        return cls.adjustStockItems(
            api,
            'transfer',
            items,
            **kwargs
        )

    @classmethod
    def assignStockItems(cls, api: inventree.api.InvenTreeAPI, items: list, customer: int, **kwargs):
        """Perform 'assign' adjustment for multiple stock items"""

        kwargs['customer'] = customer

        return cls.adjustStockItems(
            api,
            'assign',
            items,
            **kwargs
        )

    def countStock(self, quantity, **kwargs):
        """Perform a count (stocktake) action for this StockItem"""

        self.countStockItems(
            self._api,
            [
                {
                    'pk': self.pk,
                    'quantity': quantity,
                }
            ],
            **kwargs
        )

    def addStock(self, quantity, **kwargs):
        """Manually add the specified quantity to this StockItem"""

        self.addStockItems(
            self._api,
            [
                {
                    'pk': self.pk,
                    'quantity': quantity,
                }
            ],
            **kwargs
        )

    def removeStock(self, quantity, **kwargs):
        """Manually remove the specified quantity to this StockItem"""

        self.removeStockItems(
            self._api,
            [
                {
                    'pk': self.pk,
                    'quantity': quantity,
                }
            ],
            **kwargs
        )

    def transferStock(self, location, quantity=None, **kwargs):
        """Transfer this StockItem into the specified location.

        Arguments:
            location: A StockLocation instance or integer ID value
            quantity: Optionally specify quantity to transfer. If None, entire quantity is transferred
            notes: Optional transaction notes
        """

        if isinstance(location, StockLocation):
            location = location.pk

        if quantity is None:
            quantity = self.quantity

        self.transferStockItems(
            self._api,
            [
                {
                    'pk': self.pk,
                    'quantity': quantity,
                }
            ],
            location=location,
            **kwargs
        )

    def assignStock(self, customer, **kwargs):
        """Assign this stock item to a customer (by company PK)

        Arguments:
            customer: A Company instance or integer ID value
            notes: Optional transaction notes"""

        if isinstance(customer, inventree.company.Company):
            customer = customer.pk

        self.assignStockItems(
            self._api,
            [
                {
                    'item': self.pk,  # In assign API, item is used instead of item
                }
            ],
            customer=customer,
            **kwargs
        )

    def installStock(self, item, **kwargs):
        """Install the given item into this stock item

        Arguments:
            stockItem: A stockItem instance or integer ID value

        kwargs:
            quantity: quantity of installed items
            notes: Optional transaction notes"""

        if isinstance(item, StockItem):
            quantity = kwargs.get('quantity', item.quantity)
            item = item.pk
        else:
            quantity = kwargs.get('quantity', 1)

        kwargs['quantity'] = kwargs.get('quantity', quantity)
        kwargs['stock_item'] = item

        url = f"stock/{self.pk}/install/"

        return self._api.post(url, data=kwargs)

    def uninstallStock(self, location, quantity=1, **kwargs):
        """Uninstalls this item from any stock item

        Arguments:
            location: A StockLocation instance or integer ID value
            quantity: quantity of removed items. defaults to 1.
            notes: Optional transaction notes"""

        if isinstance(location, StockLocation):
            location = location.pk
        kwargs['quantity'] = quantity
        kwargs['stock_item'] = self.pk
        kwargs['location'] = location

        url = f"stock/{self.pk}/uninstall/"

        return self._api.post(url, data=kwargs)

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

    def getTrackingEntries(self, **kwargs):
        """Return list of StockItemTracking instances associated with this StockItem"""

        return StockItemTracking.list(self._api, item=self.pk, **kwargs)

    def getTestResults(self, **kwargs):
        """ Return all the test results associated with this StockItem """

        return StockItemTestResult.list(self._api, stock_item=self.pk, **kwargs)

    def uploadTestResult(self, test_name, test_result, **kwargs):
        """ Upload a test result against this StockItem """

        return StockItemTestResult.upload_result(self._api, self.pk, test_name, test_result, **kwargs)


class StockItemTracking(inventree.base.InventreeObject):
    """Class representing a StockItem tracking object."""

    URL = 'stock/track'


class StockItemTestResult(
    inventree.base.BulkDeleteMixin,
    inventree.base.MetadataMixin,
    inventree.report.ReportPrintingMixin,
    inventree.base.InventreeObject,
):
    """Class representing a StockItemTestResult object.

    Note: From API version 169 and onwards, the StockItemTestResult object
    must reference a PartTestTemplate object, rather than a test name.

    However, for backwards compatibility, test results can be uploaded using the test name,
    and will be associated with the correct PartTestTemplate on the server.
    """

    URL = 'stock/test'
    MODEL_TYPE = 'stockitem'

    def getTestTemplate(self):
        '''Return the PartTestTemplate item for this StockItemTestResult'''

        return inventree.part.PartTestTemplate(self._api, self.template)

    def getTestKey(self):

        # Get the test key from the PartTestTemplate
        return self.getTestTemplate().getTestKey()

    @classmethod
    def upload_result(cls, api, stock_item, test, result, **kwargs):
        """
        Upload a test result.

        args:
            api: Authenticated InvenTree API object
            stock_item: pk of the StockItem object to upload the test result against
            test: Name of the test (string) or ID of the test template (integer)
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
            'result': result,
            'notes': notes,
            'value': value,
        }

        # Determine the method by which the particular test is designated
        # It is either the test "name", or the test "template" ID
        if type(test) is int:
            data['template'] = test
        elif isinstance(test, inventree.part.PartTestTemplate):
            data['template'] = test.pk
        else:
            data['test'] = str(test)

        # Send the data to the server
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
