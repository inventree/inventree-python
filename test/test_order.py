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
        for prt in part.Part.list(self.api, purchaseable=True):

            # Check that the part is marked as purchaseable
            self.assertTrue(prt.purchaseable)

            # If the supplier does not have a supplier part, create one
            supplier_parts = supplier.getSuppliedParts(part=prt.pk)

            if len(supplier_parts) == 0:
                print(f"Creating supplier part for {prt.name}")

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

            self.assertEqual(line.getOrder().pk, po.pk)

            self.assertIsNotNone(line)

            # Assert that a new line item has been created
            self.assertEqual(len(po.getLineItems()), idx + 1)

            # Check that the supplier part reference is correct
            self.assertEqual(line.getSupplierPart().pk, sp.pk)

            # Check that the base part reference is correct
            self.assertEqual(line.getPart().pk, sp.part)

        for idx, line in enumerate(po.getLineItems()):
            self.assertEqual(line.quantity, idx)
            self.assertEqual(line.received, 0)


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
