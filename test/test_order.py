# -*- coding: utf-8 -*-

import os
import sys

sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from test_api import InvenTreeTestCase  # noqa: E402

from inventree import part  # noqa: E402
from inventree import order  # noqa: E402
from inventree import company  # noqa: E402


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
        ref = f"po_{n+1}_{supplier.pk}"

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

            line = po.addLineItem(part=sp.pk, quantity=idx)

            if idx == 0:
                # This will have thrown an error, as quantity = 0
                self.assertIsNone(line)
                continue

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
            'reference': f'xyz-abc-{n}',
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

            ref = f"SO_{n}_customer_{customer.pk}"

            # Create a new sales order for the company
            sales_order = customer.createSalesOrder(
                reference=ref,
                description='This is a new SalesOrder!'
            )

            self.assertEqual(len(sales_order.getLineItems()), 0)

            self.assertEqual(len(customer.getSalesOrders()), n + 1)

            # Add a line item for each saleable part
            for idx, p in enumerate(salable_parts):
                line = sales_order.addLineItem(part=p.pk, quantity=idx)

                self.assertEqual(line.quantity, idx)

                self.assertEqual(line.getPart().pk, p.pk)

                self.assertEqual(line.getOrder().pk, sales_order.pk)

                self.assertEqual(len(sales_order.getLineItems()), idx + 1)

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
                'reference': "My new sales order",
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
