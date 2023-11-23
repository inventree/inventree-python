# -*- coding: utf-8 -*-

import os
import sys

from requests.exceptions import HTTPError

sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from test_api import InvenTreeTestCase  # noqa: E402

from inventree import company  # noqa: E402
from inventree import order  # noqa: E402
from inventree import part  # noqa: E402
from inventree import stock  # noqa: E402


class POTest(InvenTreeTestCase):
    """
    Unit tests for PurchaseOrder
    """

    def test_po_fields(self):
        """
        Check that the OPTIONS endpoint provides field names for this model
        """

        field_names = order.PurchaseOrder.fieldNames(self.api)

        names = [
            'issue_date',
            'complete_date',
            'supplier',
            'status',
            'notes',
        ]

        for name in names:
            self.assertIn(name, field_names)

    def test_po_create(self):
        """
        Test purchase order creation
        """

        supplier = company.Company(self.api, pk=2)
        self.assertTrue(supplier.is_supplier)

        # Find all purchaseable parts
        parts = part.Part.list(self.api, purchaseable=True)

        for idx, prt in enumerate(parts):

            if idx >= 10:
                break

            # Check that the part is marked as purchaseable
            self.assertTrue(prt.purchaseable)

            # If the supplier does not have a supplier part, create one
            supplier_parts = supplier.getSuppliedParts(part=prt.pk)

            if len(supplier_parts) == 0:

                supplier_part = company.SupplierPart.create(
                    self.api,
                    data={
                        'part': prt.pk,
                        'supplier': supplier.pk,
                        'SKU': f"SKU-{supplier.pk}-{prt.name}",
                        'MPN': f"MPN-{supplier.pk}-{prt.name}",
                    }
                )

                self.assertIsNotNone(supplier_part)
                self.assertIsNotNone(supplier_part.pk)

        parts = supplier.getSuppliedParts()

        # There should be at least *some* supplied parts
        self.assertTrue(len(parts) > 0)

        # Create a purchase order
        n = len(order.PurchaseOrder.list(self.api))

        # Create a PO with unique reference
        ref = f"PO-{n+1}"

        po = supplier.createPurchaseOrder(
            reference=ref,
            description="This is a PO created using the Python interface"
        )

        self.assertIsNotNone(po)
        self.assertIsNotNone(po.pk)

        found = False

        # Ensure that we can find the pk of the new order
        for _order in supplier.getPurchaseOrders():
            if _order.pk == po.pk:
                found = True
                break

        self.assertTrue(found)

        # Should not be any line-items yet!
        items = po.getLineItems()
        self.assertEqual(len(items), 0)

        # Let's add some!
        supplier_parts = supplier.getSuppliedParts()

        for idx, sp in enumerate(supplier_parts):

            if idx == 0:
                with self.assertRaises(HTTPError):
                    line = po.addLineItem(part=sp.pk, quantity=idx)
                continue

            line = po.addLineItem(part=sp.pk, quantity=idx)

            self.assertEqual(line.getOrder().pk, po.pk)

            self.assertIsNotNone(line)

            # Assert that a new line item has been created
            self.assertEqual(len(po.getLineItems()), idx)

            # Check that the supplier part reference is correct
            self.assertEqual(line.getSupplierPart().pk, sp.pk)

            # Check that the base part reference is correct
            self.assertEqual(line.getPart().pk, sp.part)

        for idx, line in enumerate(po.getLineItems()):
            self.assertEqual(line.quantity, idx + 1)
            self.assertEqual(line.received, 0)
            line.delete()

        # Assert length is now one less than before
        self.assertEqual(len(po.getLineItems()), 0)

        # Should not be any extra-line-items yet!
        extraitems = po.getExtraLineItems()
        self.assertEqual(len(extraitems), 0)

        # Let's add some!
        extraline = po.addExtraLineItem(quantity=1, reference="Transport costs", notes="Extra line item added from Python interface", price=10, price_currency="EUR")

        self.assertEqual(extraline.getOrder().pk, po.pk)

        self.assertIsNotNone(extraline)

        # Assert that a new line item has been created
        self.assertEqual(len(po.getExtraLineItems()), 1)

        # Assert that we can delete the item again
        extraline.delete()

        # Now there should be 0 lines left
        self.assertEqual(len(po.getExtraLineItems()), 0)

    def test_order_cancel(self):
        """Test that we can cancel a PurchaseOrder via the API"""

        n = len(order.PurchaseOrder.list(self.api)) + 1
        ref = f"PO-{n}"

        # Create a new PO
        po = order.PurchaseOrder.create(self.api, data={
            'supplier': 1,
            'reference': ref,
            'description': 'Some new order'
        })

        self.assertEqual(po.status, 10)
        self.assertEqual(po.status_text, "Pending")

        # Cancel the order
        po.cancel()

        self.assertEqual(po.status, 40)
        self.assertEqual(po.status_text, "Cancelled")

    def test_order_complete_with_receive(self):
        """Test that we can complete an order via the API, after receiving
        items via API"""

        n = len(order.PurchaseOrder.list(self.api)) + 1
        ref = f"PO-{n}"

        # First, let's create a new PurchaseOrder
        po = order.PurchaseOrder.create(self.api, data={
            'supplier': 1,
            'reference': ref,
            'description': 'A purchase order with items to be received',
        })

        # Get first location
        use_location = stock.StockLocation.list(self.api, limit=1)[0]

        # Add some line items
        for p in company.SupplierPart.list(self.api, supplier=1, limit=5):
            po.addLineItem(
                part=p.pk,
                quantity=10,
                destination=use_location.pk
            )

        # Check that lines have actually been added
        lines = po.getLineItems()
        self.assertTrue(len(lines) > 0)

        # Initial status code is "PENDING"
        self.assertEqual(po.status, 10)
        self.assertEqual(po.status_text, "Pending")

        # Receive lines too early, assert error
        with self.assertRaises(HTTPError):
            po.receiveAll(location=1)

        # Issue the order
        po.issue()
        po.reload()

        self.assertEqual(po.status, 20)
        self.assertEqual(po.status_text, "Placed")

        # Try to complete the order (should fail, as lines have not been received)
        with self.assertRaises(HTTPError):
            po.complete()

        po.reload()

        # Check that order status has *not* changed
        self.assertEqual(po.status, 20)

        # Prepare one line item for special treatment
        po_line_0 = po.getLineItems()[0]

        # Get list of items currently in stock, for comparison later
        stock_items_before = stock.StockItem.list(self.api, supplier_part=po_line_0.part, location=use_location.pk)
        pks_before = [x.pk for x in stock_items_before]

        # Now, receive some of one of the line item with status ATTENTION
        po_line_0.receive(status=50, quantity=5)

        # Get new list of stock items
        stock_items_after = stock.StockItem.list(self.api, supplier_part=po_line_0.part, location=use_location.pk)
        pks_after = [x.pk for x in stock_items_after]

        # make sure a stock item has been added
        self.assertEqual(len(pks_after), len(pks_before) + 1)

        # Get the newly added PK and stock item
        newpk = list(set(pks_after) - set(pks_before))[0]
        new_stock_item = stock.StockItem(self.api, pk=newpk)

        # Check the last stock item for the expected quantity and status
        self.assertEqual(new_stock_item.quantity, 5)
        self.assertEqual(new_stock_item.status, 50)

        # Receive the rest of this item, with defaults
        po_line_0.receive()

        # Receive all line items
        # Use the ID of the location here
        result = po.receiveAll(location=use_location.pk)

        # Check the result returned
        self.assertIsInstance(result, dict)
        self.assertIn('items', result)
        self.assertIn('location', result)
        # Check that all except one line were marked
        self.assertEqual(len(result['items']), len(po.getLineItems()) - 1)

        # Receive all line items again - make sure answer is None
        # use the StockLocation item here
        result = po.receiveAll(location=use_location)
        self.assertIsNone(result)

        # Complete the order, do not accept any incomplete lines
        po.complete(accept_incomplete=False)
        po.reload()

        # Check that the order is now complete
        self.assertEqual(po.status, 30)

    def test_order_complete(self):
        """Test that we can complete an order via the API, with un-finished items remaining"""

        n = len(order.PurchaseOrder.list(self.api)) + 1
        ref = f"PO-{n}"

        # First, let's create a new PurchaseOrder
        po = order.PurchaseOrder.create(self.api, data={
            'supplier': 1,
            'reference': ref,
            'description': 'A new purchase order',
        })

        # Add some line items
        for p in company.SupplierPart.list(self.api, supplier=1, limit=5):

            po.addLineItem(
                part=p.pk,
                quantity=10,
            )

        # Check that lines have actually been added
        lines = po.getLineItems()
        self.assertTrue(len(lines) > 0)

        # Initial status code is "PENDING"
        self.assertEqual(po.status, 10)
        self.assertEqual(po.status_text, "Pending")

        # Issue the order
        po.issue()
        po.reload()

        self.assertEqual(po.status, 20)
        self.assertEqual(po.status_text, "Placed")

        # Try to complete the order (should fail, as lines have not been received)
        with self.assertRaises(HTTPError):
            po.complete()

        po.reload()

        # Check that order status has *not* changed
        self.assertEqual(po.status, 20)

        # Now, try to complete the order again, accepting incomplete
        po.complete(accept_incomplete=True)
        po.reload()

        # Check that the order is now complete
        self.assertEqual(po.status, 30)

    def test_purchase_order_delete(self):
        """
        Test that we can delete existing purchase orders
        """

        orders = order.PurchaseOrder.list(self.api)

        self.assertTrue(len(orders) > 0)

        for po in orders:
            po.delete()

        orders = order.PurchaseOrder.list(self.api)
        self.assertEqual(len(orders), 0)

    def test_po_attachment(self):
        """
        Test upload of attachment against a PurchaseOrder
        """

        # Ensure we have a least one purchase order to work with
        n = len(order.PurchaseOrder.list(self.api))

        po = order.PurchaseOrder.create(self.api, {
            'supplier': 1,
            'reference': f'PO-{n + 100}',
            'description': 'A new purchase order',
        })

        attachments = po.getAttachments()
        self.assertEqual(len(attachments), 0)

        # Test we can upload an attachment against this PurchaseOrder
        fn = os.path.join(os.path.dirname(__file__), 'attachment.txt')

        # Should be able to upload the same file multiple times!
        for i in range(3):
            response = po.uploadAttachment(fn, comment='Test upload to purchase order')
            self.assertEqual(response['comment'], 'Test upload to purchase order')

        # Test that an invalid file raises an error
        with self.assertRaises(FileNotFoundError):
            po.uploadAttachment('not_found.txt')

        # Test that missing the 'order' parameter fails too
        with self.assertRaises(ValueError):
            order.PurchaseOrderAttachment.upload(self.api, fn, comment='Should not work!')

        # Check that attachments uploaded OK
        attachments = order.PurchaseOrderAttachment.list(self.api, order=po.pk)
        self.assertEqual(len(attachments), 3)


class SOTest(InvenTreeTestCase):
    """
    Unit test for SalesOrder
    """

    def test_so_fields(self):
        """
        Check that the OPTIONS endpoint provides field names for this model
        """

        names = [
            'customer',
            'description',
            'overdue',
            'reference',
        ]

        fields = order.SalesOrder.fieldNames(self.api)

        for name in names:
            self.assertIn(name, fields)

    def test_so_create(self):
        """
        Test sales order creation
        """

        # Create some salable parts (if none exist)

        if len(part.Part.list(self.api, salable=True)) == 0:

            for idx in range(10):

                part.Part.create(
                    self.api,
                    {
                        'name': f"SellPart_{idx}",
                        'description': "A saleable part",
                        'salable': True,
                        'category': 1,
                        'active': True,
                        'IPN': f"PART_{idx}",
                        'revision': 'A',
                    }
                )

        # Find all saleable parts
        salable_parts = part.Part.list(self.api, salable=True)

        # For each customer
        for customer in company.Company.list(self.api, is_customer=True):

            self.assertTrue(customer.is_customer)
            self.assertTrue(len(salable_parts) > 0)

            # Create a new sales order for this customer
            n = len(customer.getSalesOrders())

            # Create a new sales order for the company
            sales_order = customer.createSalesOrder(
                description='This is a new SalesOrder!'
            )

            self.assertIsNotNone(sales_order)

            self.assertEqual(len(sales_order.getLineItems()), 0)

            self.assertEqual(len(customer.getSalesOrders()), n + 1)

            # Add a line item for each saleable part
            for idx, p in enumerate(salable_parts):
                line = sales_order.addLineItem(part=p.pk, quantity=idx)

                self.assertEqual(line.quantity, idx)

                self.assertEqual(line.getPart().pk, p.pk)

                self.assertEqual(line.getOrder().pk, sales_order.pk)

                self.assertEqual(len(sales_order.getLineItems()), idx + 1)

            # Should not be any extra-line-items yet!
            self.assertEqual(len(sales_order.getExtraLineItems()), 0)

            # Let's add some!
            extraline = sales_order.addExtraLineItem(
                quantity=1,
                reference="Transport costs",
                notes="Extra line item added from Python interface",
                price=10, price_currency="EUR"
            )

            self.assertIsNotNone(extraline)

            self.assertEqual(extraline.getOrder().pk, sales_order.pk)

            # Assert that a new line item has been created
            self.assertEqual(len(sales_order.getExtraLineItems()), 1)

            # Assert that we can delete the item again
            extraline.delete()

            # Now there should be 0 lines left
            self.assertEqual(len(sales_order.getExtraLineItems()), 0)

    def test_so_attachment(self):
        """
        Test upload of attachment against a SalesOrder
        """

        # Grab the first available SalesOrder
        orders = order.SalesOrder.list(self.api)

        if len(orders) > 0:
            so = orders[0]
        else:
            so = order.SalesOrder.create(self.api, {
                'customer': 4,
                "description": "Selling some stuff",
            })

        n = len(so.getAttachments())

        # Upload a new attachment
        fn = os.path.join(os.path.dirname(__file__), 'attachment.txt')
        response = so.uploadAttachment(fn, comment='Sales order attachment')

        pk = response['pk']

        attachment = order.SalesOrderAttachment(self.api, pk=pk)

        self.assertEqual(attachment.order, so.pk)
        self.assertEqual(attachment.comment, 'Sales order attachment')

        attachments = order.SalesOrderAttachment.list(self.api, order=so.pk)
        self.assertEqual(len(attachments), n + 1)

    def test_so_shipment(self):
        """Test shipment functionality for a SalesOrder."""

        # Construct a new SalesOrder instance
        so = order.SalesOrder.create(self.api, {
            'customer': 4,
            "description": "Selling some stuff",
        })

        # Add some line items to the SalesOrder
        for p in part.Part.list(self.api, is_template=False, salable=True, limit=5):

            # Create a line item matching the part
            order.SalesOrderLineItem.create(
                self.api,
                data={
                    'part': p.pk,
                    'order': so.pk,
                    'quantity': 10,
                }
            )

            # Ensure there is available stock
            stock.StockItem.create(
                self.api,
                data={
                    'part': p.pk,
                    'quantity': 25,
                    'location': 1,
                }
            )

        # The shipments list should return something which is not none
        self.assertIsNotNone(so.getShipments())

        # Count number of current shipments
        num_shipments = len(so.getShipments())

        # Create a new shipment - without data, use SalesOrderShipment method
        with self.assertRaises(TypeError):
            shipment_1 = order.SalesOrderShipment.create(self.api)

        # Create new shipment - minimal data, use SalesOrderShipment method
        shipment_1 = order.SalesOrderShipment.create(
            self.api, data={
                'order': so.pk,
                'reference': f'Package {num_shipments+1}'
            }
        )

        # Assert the shipment is created
        self.assertIsNotNone(shipment_1)

        # Assert the shipment Order is equal to the expected one
        self.assertEqual(shipment_1.getOrder().pk, so.pk)

        # Count number of current shipments
        self.assertEqual(len(so.getShipments()), num_shipments + 1)
        num_shipments = len(so.getShipments())

        # Create new shipment - use addShipment method.
        # Should fail because reference will not be unique
        with self.assertRaises(HTTPError):
            shipment_2 = so.addShipment(f'Package {num_shipments}')

        # Create new shipment - use addShipment method. No extra data
        shipment_2 = so.addShipment(f'Package {num_shipments+1}')

        # Assert the shipment is not created
        self.assertIsNotNone(shipment_2)

        # Assert the shipment Order is equal to the expected one
        self.assertEqual(shipment_2.getOrder().pk, so.pk)

        # Assert shipment reference is as expected
        self.assertEqual(shipment_2.reference, f'Package {num_shipments+1}')

        # Count number of current shipments
        self.assertEqual(len(so.getShipments()), num_shipments + 1)
        num_shipments = len(so.getShipments())

        # Create another shipment - use addShipment method.
        # With some extra data, including non-sense order
        # (which should be overwritten)
        notes = f'Test shipment number {num_shipments+1} for order {so.pk}'
        tracking_number = '93414134343'

        shipment_2 = so.addShipment(
            reference=f'Package {num_shipments+1}',
            order=10103413,
            notes=notes,
            tracking_number=tracking_number
        )

        # Assert the shipment is created
        self.assertIsNotNone(shipment_2)

        # Assert the shipment Order is equal to the expected one
        self.assertEqual(shipment_2.getOrder().pk, so.pk)

        # Assert shipment reference is as expected
        self.assertEqual(shipment_2.reference, f'Package {num_shipments+1}')

        # Make sure extra data is also as expected
        self.assertEqual(shipment_2.notes, notes)
        self.assertEqual(shipment_2.tracking_number, tracking_number)

        # Count number of current shipments
        self.assertEqual(len(so.getShipments()), num_shipments + 1)
        num_shipments = len(so.getShipments())

        # Remember for later test
        allocated_quantities = dict()

        # Assign each line item to this shipment
        for si in so.getLineItems():
            # If there is no stock available, delete this line
            if si.available_stock == 0:
                si.delete()
            else:
                response = si.allocateToShipment(shipment_2)
                # Remember what we are doing for later check
                # a response of None means nothing was allocated
                if response is not None:
                    allocated_quantities[si.pk] = (
                        {x['stock_item']: float(x['quantity']) for x in response['items']}
                    )

        # Check saved values
        for so_part in so.getLineItems():
            if so_part.pk in allocated_quantities:
                if len(allocated_quantities[so_part.pk]) > 0:
                    self.assertEqual(
                        {x['item']: float(x['quantity']) for x in shipment_2.allocations if x['line'] == so_part.pk},
                        allocated_quantities[so_part.pk]
                    )

        # Attempt to complete the shipment, but no items have been allocated
        shipment_2.complete()

        # Make sure date is not None
        self.assertIsNotNone(shipment_2.shipment_date)

        # Try to complete this order
        # Ship remaining shipments first
        for shp in so.getShipments():
            # Delete shipment if it has no allocations
            if len(shp.allocations) == 0:
                shp.delete()
                continue
            # If the shipment has no date, try to mark it shipped
            if shp.shipment_date is None:
                shp.ship()
        so.complete()
        self.assertEqual(so.status, 20)
        self.assertEqual(so.status_text, 'Shipped')

    def test_order_cancel(self):
        """Test cancel sales order"""

        so = order.SalesOrder.create(self.api, {
            'customer': 4,
            "description": "Selling some more stuff",
        })

        so.cancel()

        self.assertEqual(so.status, 40)
        self.assertEqual(so.status_text, 'Cancelled')


class ROTest(InvenTreeTestCase):
    """Unit tests for ReturnOrder models"""

    def test_ro_fields(self):
        """Check the OPTIONS endpoints for return order models"""

        field_names = order.ReturnOrder.fieldNames(self.api)

        names = [
            'contact',
            'line_items',
            'link',
            'overdue',
            'customer',
            'status',
            'reference'
        ]

        for name in names:
            self.assertIn(name, field_names)

    def test_ro_create(self):
        """Test that we can create a ReturnOrder"""

        customer = company.Company(self.api, pk=4)
        self.assertTrue(customer.is_customer)

        n = len(order.ReturnOrder.list(self.api))
        ref = f"RMA-00{n}"

        # Create a new ReturnOrder
        ro = customer.createReturnOrder(
            reference=ref,
            description="A new return order"
        )

        self.assertIsNotNone(ro)
        self.assertIsNotNone(ro.pk)

        # Check line items (should be zero)
        items = ro.getLineItems()
        self.assertEqual(len(items), 0)

        # Check extra line items (should be zero)
        items = ro.getExtraLineItems()
        self.assertEqual(len(items), 0)

        # Create some extra items
        for idx in range(3):
            ro.addExtraLineItem(
                reference=f"ref {idx}",
                notes="my notes",
            )

        self.assertEqual(len(ro.getExtraLineItems()), 3)

        for line in ro.getExtraLineItems():
            lo = line.getOrder()
            self.assertEqual(lo.pk, ro.pk)

        self.assertEqual(ro.getCustomer().pk, 4)
        self.assertIsNone(ro.getContact())

        # Test that we can "edit" the order
        self.assertEqual(ro.reference, ref)

        ro.save(data={
            'reference': 'RMA-99999',
        })

        ro.reload()
        self.assertEqual(ro.reference, 'RMA-99999')

        # Now, delete it
        ro.delete()

        # Should throw an error, as it no longer exists
        with self.assertRaises(HTTPError):
            ro.reload()

    def test_ro_cancel(self):
        """Test that an order can be cancelled"""

        ro = order.ReturnOrder.create(self.api, data={
            'description': 'To be cancelled',
            'customer': 4,
        })
        # Order should initially be 'pending'
        self.assertEqual(ro.status, 10)
        ro.cancel()
        ro.reload()
        # Order should now be 'cancelled'
        self.assertEqual(ro.status, 40)

    def test_ro_issue(self):
        """Test that an order can be issued"""

        ro = order.ReturnOrder.create(self.api, data={
            'description': 'To be issued',
            'customer': 4,
        })

        # Order should initially be 'pending'
        self.assertEqual(ro.status, 10)
        ro.issue()
        ro.reload()
        # Order should now be 'in progress'
        self.assertEqual(ro.status, 20)

    def test_ro_complete(self):
        """Test that an order can be completed"""

        ro = order.ReturnOrder.create(self.api, data={
            'description': 'To be completed',
            'customer': 4,
        })
        ro.issue()
        ro.complete()
        ro.reload()
        # Order should now be 'complete'
        self.assertEqual(ro.status, 30)
