"""
Sales Order models
"""

import inventree.base
import inventree.company
import inventree.part
import inventree.report
import inventree.stock


class SalesOrder(
    inventree.base.AttachmentMixin,
    inventree.base.MetadataMixin,
    inventree.base.StatusMixin,
    inventree.report.ReportPrintingMixin,
    inventree.base.InventreeObject,
):
    """ Class representing the SalesOrder database model """

    URL = 'order/so'
    MODEL_TYPE = 'salesorder'

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
        """ Return the line items associated with this order """
        return SalesOrderLineItem.list(self._api, order=self.pk, **kwargs)

    def getExtraLineItems(self, **kwargs):
        """ Return the line items associated with this order """
        return SalesOrderExtraLineItem.list(self._api, order=self.pk, **kwargs)

    def addLineItem(self, **kwargs):
        """
        Create (and return) new SalesOrderLineItem object against this SalesOrder
        """

        kwargs['order'] = self.pk

        return SalesOrderLineItem.create(self._api, data=kwargs)

    def addExtraLineItem(self, **kwargs):
        """
        Create (and return) new SalesOrderExtraLineItem object against this SalesOrder
        """

        kwargs['order'] = self.pk

        return SalesOrderExtraLineItem.create(self._api, data=kwargs)

    def getShipments(self, **kwargs):
        """ Return the shipments associated with this order """

        return SalesOrderShipment.list(self._api, order=self.pk, **kwargs)

    def addShipment(self, reference, **kwargs):
        """ Create (and return) new SalesOrderShipment
        against this SalesOrder """

        kwargs['order'] = self.pk
        kwargs['reference'] = reference

        return SalesOrderShipment.create(self._api, data=kwargs)

    def issue(self, **kwargs):
        """Issue (send) this order"""
        return self._statusupdate(status='issue', **kwargs)

    def hold(self, **kwargs):
        """Place this order on hold"""
        return self._statusupdate(status='hold', **kwargs)

    def cancel(self, **kwargs):
        """Cancel this order"""
        return self._statusupdate(status='cancel', **kwargs)


class SalesOrderLineItem(
    inventree.base.InventreeObject,
    inventree.base.MetadataMixin,
):
    """ Class representing the SalesOrderLineItem database model """

    URL = 'order/so-line'

    def getPart(self):
        """
        Return the Part object referenced by this SalesOrderLineItem
        """
        return inventree.part.Part(self._api, self.part)

    def getOrder(self):
        """
        Return the SalesOrder to which this SalesOrderLineItem belongs
        """
        return SalesOrder(self._api, self.order)

    def allocateToShipment(self, shipment, stockitems=None, quantity=None):
        """
        Assign the items of this line to the given shipment.

        By default, assign the total quantity using the first stock
        item(s) found. As many items as possible, up to the quantity in
        sales order, are assigned.

        To limit which stock items can be used, supply a list of stockitems
        to use in the argument stockitems.

        To limit how many items are assigned, supply a quantity to the
        argument quantity. This can also be used to over-assign the items,
        as no check for the amounts in the sales order is performed.

        This function returns a list of items assigned during this call.
        If nothing is returned, this means that nothing was assigned,
        possibly because no stock items are available.
        """

        # If stockitems are not defined, get the list of available stock items
        if stockitems is None:
            stockitems = self.getPart().getStockItems(include_variants=False, in_stock=True, available=True)

        # If no quantity is defined, calculate the number of required items
        # This is the number of sold items not yet allocated, but can not
        # be higher than the number of allocated items
        if quantity is None:
            required_amount = min(
                self.quantity - self.allocated, self.available_stock
            )

        else:
            try:
                required_amount = int(quantity)
            except ValueError:
                raise ValueError(
                    "Argument quantity must be convertible to an integer"
                )

        # Look through stock items, assign items until the required amount
        # is reached
        items = list()

        for SI in stockitems:

            # Check if we are done
            if required_amount <= 0:
                continue

            # Check that this item has available stock
            if SI.quantity - SI.allocated > 0:
                thisitem = {
                    "line_item": self.pk,
                    "quantity": min(
                        required_amount, SI.quantity - SI.allocated
                    ),
                    "stock_item": SI.pk
                }

                # Correct the required amount
                required_amount -= thisitem["quantity"]

                # Append
                items.append(thisitem)

        # Use SalesOrderShipment method to perform allocation
        if len(items) > 0:
            return shipment.allocateItems(items)


class SalesOrderExtraLineItem(
    inventree.base.InventreeObject,
    inventree.base.MetadataMixin,
):
    """ Class representing the SalesOrderExtraLineItem database model """

    URL = 'order/so-extra-line'

    def getOrder(self):
        """
        Return the SalesOrder to which this SalesOrderLineItem belongs
        """
        return SalesOrder(self._api, self.order)


class SalesOrderAllocation(
    inventree.base.InventreeObject
):
    """Class representing the SalesOrderAllocation database model."""

    MIN_API_VERSION = 267
    URL = 'order/so-allocation'

    def getOrder(self):
        """Return the SalesOrder to which this SalesOrderAllocation belongs."""
        return SalesOrder(self._api, self.order)

    def getShipment(self):
        """Return the SalesOrderShipment to which this SalesOrderAllocation belongs."""
        from sales_order import SalesOrderShipment
        return SalesOrderShipment(self._api, self.shipment)

    def getLineItem(self):
        """Return the SalesOrderLineItem to which this SalesOrderAllocation belongs."""
        return SalesOrderLineItem(self._api, self.line)

    def getStockItem(self):
        """Return the StockItem to which this SalesOrderAllocation belongs."""
        return inventree.stock.StockItem(self._api, self.item)

    def getPart(self):
        """Return the Part to which this SalesOrderAllocation belongs."""
        return inventree.part.Part(self._api, self.part)


class SalesOrderShipment(
    inventree.base.InventreeObject,
    inventree.base.StatusMixin,
    inventree.base.MetadataMixin,
):
    """Class representing a shipment for a SalesOrder"""

    URL = 'order/so/shipment'

    def getOrder(self):
        """Return the SalesOrder to which this SalesOrderShipment belongs."""
        return SalesOrder(self._api, self.order)

    def allocateItems(self, items=[]):
        """
        Function to allocate items to the current shipment

        items is expected to be a list containing dicts, one for each item
        to be assigned. Each dict should contain three parameters, as
        follows:
            items = [{
                "line_item": 25,
                "quantity": 150,
                "stock_item": 26
            }
        """

        # Customize URL
        url = f'order/so/{self.getOrder().pk}/allocate'

        # Create data from given inputs
        data = {
            'items': items,
            'shipment': self.pk
        }

        # Send data
        response = self._api.post(url, data)

        # Reload
        self.reload()

        # Return
        return response

    def getAllocations(self):
        """Return the allocations associated with this shipment"""
        return SalesOrderAllocation.list(self._api, shipment=self.pk)

    @property
    def allocations(self):
        """Return the allocations associated with this shipment.

        Note: This is an overload of getAllocations() method, for legacy compatibility.
        """
        try:
            return self.getAllocations()
        except NotImplementedError:
            return self._data['allocations']

    def complete(
        self,
        shipment_date=None,
        tracking_number='',
        invoice_number='',
        link='',
        **kwargs
    ):
        """
        Complete the shipment, with given shipment_date, or reasonable
        defaults.
        """

        # Create data from given inputs
        data = {
            'shipment_date': shipment_date,
            'tracking_number': tracking_number,
            'invoice_number': invoice_number,
            'link': link
        }

        # Return
        return self._statusupdate(status='ship', data=data, **kwargs)

    def ship(self, *args, **kwargs):
        """Alias for complete function"""
        self.complete(*args, **kwargs)
