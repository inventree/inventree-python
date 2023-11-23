"""
ReturnOrder models
"""

import inventree.base
import inventree.company
import inventree.part
import inventree.report
import inventree.stock


class ReturnOrder(
    inventree.base.MetadataMixin,
    inventree.base.InventreeObject,
    inventree.base.StatusMixin,
    inventree.report.ReportPrintingMixin,
):
    """Class representing the ReturnOrder database model"""

    URL = 'order/ro'
    REQUIRED_API_VERSION = 104

    # Setup for Report mixin
    REPORTNAME = 'ro'
    REPORTITEM = 'order'

    def getCustomer(self):
        """Return the customer associated with this order"""
        return inventree.company.Company(self._api, self.customer)

    def getContact(self):
        """Return the contact associated with this order"""
        if self.contact is not None:
            return inventree.company.Contact(self._api, self.contact)
        else:
            return None

    def getLineItems(self, **kwargs):
        """Return line items associated with this order"""
        return ReturnOrderLineItem.list(self._api, order=self.pk, **kwargs)

    def addLineItem(self, **kwargs):
        """Create (and return) a new ReturnOrderLineItem against this order"""
        kwargs['order'] = self.pk
        return ReturnOrderLineItem.create(self._api, data=kwargs)

    def getExtraLineItems(self, **kwargs):
        """Return the extra line items associated with this order"""
        return ReturnOrderExtraLineItem.list(self._api, order=self.pk, **kwargs)

    def addExtraLineItem(self, **kwargs):
        """Create (and return) a new ReturnOrderExtraLineItem against this order"""
        kwargs['order'] = self.pk
        return ReturnOrderExtraLineItem.create(self._api, data=kwargs)

    def getAttachments(self):
        """Return a list of attachments associated with this order"""
        return ReturnOrderAttachment.list(self._api, order=self.pk)

    def uploadAttachment(self, attachment, comment=''):
        """Upload a file attachment against this order"""
        return ReturnOrderAttachment.upload(
            self._api,
            attachment,
            comment=comment,
            order=self.pk
        )

    def issue(self, **kwargs):
        """Issue (send) this order"""
        return self._statusupdate(status='issue', **kwargs)

    def cancel(self, **kwargs):
        """Cancel this order"""
        return self._statusupdate(status='cancel', **kwargs)

    def complete(self, **kwargs):
        """Mark this order as complete"""
        return self._statusupdate(status='complete', **kwargs)


class ReturnOrderLineItem(inventree.base.InventreeObject):
    """Class representing the ReturnOrderLineItem model"""

    URL = 'order/ro-line/'
    REQUIRED_API_VERSION = 104

    def getOrder(self):
        """Return the ReturnOrder to which this ReturnOrderLineItem belongs"""
        return ReturnOrder(self._api, self.order)

    def getStockItem(self):
        """Return the StockItem associated with this line item"""
        return inventree.stock.StockItem(self._api, self.item)


class ReturnOrderExtraLineItem(inventree.base.InventreeObject):
    """Class representing the ReturnOrderExtraLineItem model"""

    URL = 'order/ro-extra-line/'
    REQUIRED_API_VERSION = 104

    def getOrder(self):
        """Return the ReturnOrder to which this line item belongs"""
        return ReturnOrder(self._api, self.order)


class ReturnOrderAttachment(inventree.base.InventreeObject):
    """Class representing the ReturnOrderAttachment model"""

    URL = 'order/ro/attachment'
    REQUIRED_KWARGS = ['order']
    REQUIRED_API_VERSION = 104
