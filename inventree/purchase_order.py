"""
PurchaseOrder models
"""

import inventree.base
import inventree.company
import inventree.part
import inventree.report


class PurchaseOrder(
    inventree.base.MetadataMixin,
    inventree.base.InventreeObject,
    inventree.base.StatusMixin,
    inventree.report.ReportPrintingMixin,
):
    """ Class representing the PurchaseOrder database model """

    URL = 'order/po'

    # Setup for Report mixin
    REPORTNAME = 'po'
    REPORTITEM = 'order'

    def getSupplier(self):
        """Return the supplier (Company) associated with this order"""
        return inventree.company.Company(self._api, self.supplier)

    def getContact(self):
        """Return the contact associated with this order"""
        if self.contact is not None:
            return inventree.company.Contact(self._api, self.contact)
        else:
            return None

    def getLineItems(self, **kwargs):
        """ Return the line items associated with this order """
        return PurchaseOrderLineItem.list(self._api, order=self.pk, **kwargs)

    def getExtraLineItems(self, **kwargs):
        """ Return the line items associated with this order """
        return PurchaseOrderExtraLineItem.list(self._api, order=self.pk, **kwargs)

    def addLineItem(self, **kwargs):
        """
        Create (and return) new PurchaseOrderLineItem object against this PurchaseOrder
        """

        kwargs['order'] = self.pk

        return PurchaseOrderLineItem.create(self._api, data=kwargs)

    def addExtraLineItem(self, **kwargs):
        """
        Create (and return) new PurchaseOrderExtraLineItem object against this PurchaseOrder
        """

        kwargs['order'] = self.pk

        return PurchaseOrderExtraLineItem.create(self._api, data=kwargs)

    def getAttachments(self):
        return PurchaseOrderAttachment.list(self._api, order=self.pk)

    def uploadAttachment(self, attachment, comment=''):
        return PurchaseOrderAttachment.upload(
            self._api,
            attachment,
            comment=comment,
            order=self.pk,
        )

    def issue(self, **kwargs):
        """
        Issue the purchase order
        """

        # Return
        return self._statusupdate(status='issue', **kwargs)

    def receiveAll(self, location, status=10):
        """
        Receive all of the purchase order items, into the given location.

        Note that the location may be overwritten if a destination is saved in the PO for the line item.

        By default, the status is set to OK (Code 10).

        To modify the defaults, use the arguments:
            status: Status code
                    10 OK
                    50 ATTENTION
                    55 DAMAGED
                    60 DESTROYED
                    65 REJECTED
                    70 LOST
                    75 QUARANTINED
                    85 RETURNED
        """

        # Check if location is a model - or try to get an integer
        try:
            location_id = location.pk
        except:  # noqa:E722
            location_id = int(location)

        # Prepare request data
        items = list()
        for li in self.getLineItems():
            quantity_to_receive = li.quantity - li.received
            # Make sure quantity > 0
            if quantity_to_receive > 0:
                items.append(
                    {
                        'line_item': li.pk,
                        'supplier_part': li.part,
                        'quantity': quantity_to_receive,
                        'status': status,
                        'location': location_id,
                    }
                )

        # If nothing is left, quit here
        if len(items) < 1:
            return None

        data = {
            'items': items,
            'location': location_id
        }

        # Set the url
        URL = f"{self.URL}/{self.pk}/receive/"

        # Send data
        response = self._api.post(URL, data)

        # Reload
        self.reload()

        # Return
        return response


class PurchaseOrderLineItem(
    inventree.base.InventreeObject,
    inventree.base.MetadataMixin,
):
    """ Class representing the PurchaseOrderLineItem database model """

    URL = 'order/po-line'

    def getSupplierPart(self):
        """
        Return the SupplierPart associated with this PurchaseOrderLineItem
        """
        return inventree.company.SupplierPart(self._api, self.part)

    def getPart(self):
        """
        Return the Part referenced by the associated SupplierPart
        """
        return inventree.part.Part(self._api, self.getSupplierPart().part)

    def getOrder(self):
        """
        Return the PurchaseOrder to which this PurchaseOrderLineItem belongs
        """
        return PurchaseOrder(self._api, self.order)

    def receive(self, quantity=None, status=10, location=None, batch_code='', serial_numbers=''):
        """
        Mark this line item as received.

        By default, receives all remaining items in the order, and puts them in the destination defined in the PO.
        The status is set to OK (Code 10).

        To modify the defaults, use the arguments:
            quantity: Number of units to receive. If None, will calculate the quantity not yet received and receive these.
            status: Status code
                    10 OK
                    50 ATTENTION
                    55 DAMAGED
                    60 DESTROYED
                    65 REJECTED
                    70 LOST
                    75 QUARANTINED
                    85 RETURNED
            location: Location ID, or a StockLocation item

        If given, the following arguments are also sent as parameters:
            batch_code
            serial_numbers
        """

        if quantity is None:
            # Subtract number of already received lines from the order quantity
            quantity = self.quantity - self.received

        if location is None:
            location_id = self.destination
        else:
            # Check if location is a model - or try to get an integer
            try:
                location_id = location.pk
            except:  # noqa:E722
                location_id = int(location)

        # Prepare request data
        data = {
            'items': [
                {
                    'line_item': self.pk,
                    'supplier_part': self.part,
                    'quantity': quantity,
                    'status': status,
                    'location': location_id,
                    'batch_code': batch_code,
                    'serial_numbers': serial_numbers
                }
            ],
            'location': location_id
        }

        # Set the url
        URL = f"{self.getOrder().URL}/{self.getOrder().pk}/receive/"

        # Send data
        response = self._api.post(URL, data)

        # Reload
        self.reload()

        # Return
        return response


class PurchaseOrderExtraLineItem(
    inventree.base.InventreeObject,
    inventree.base.MetadataMixin,
):
    """ Class representing the PurchaseOrderExtraLineItem database model """

    URL = 'order/po-extra-line'

    def getOrder(self):
        """
        Return the PurchaseOrder to which this PurchaseOrderLineItem belongs
        """
        return PurchaseOrder(self._api, self.order)


class PurchaseOrderAttachment(inventree.base.Attachment):
    """Class representing a file attachment for a PurchaseOrder"""

    URL = 'order/po/attachment'
    REQUIRED_KWARGS = ['order']
