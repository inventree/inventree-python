# -*- coding: utf-8 -*-

import os
import sys

sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from inventree import company  # noqa: E402
from test_api import InvenTreeTestCase  # noqa: E402


class CompanyTest(InvenTreeTestCase):
    """
    Test that Company related objects can be managed via the API
    """

    def test_fields(self):
        """
        Test field names via OPTIONS request
        """

        field_names = company.Company.fieldNames(self.api)

        for field in [
            'url',
            'name',
            'image',
            'is_customer',
            'is_manufacturer',
            'is_supplier'
        ]:
            self.assertIn(field, field_names)

    def test_company_create(self):
        c = company.Company(self.api, {
            'name': 'Company',
        })

        self.assertIsNotNone(c)

    def test_company_parts(self):
        """
        Tests that the 'supplied' and 'manufactured' parts can be retrieved
        """

        c = company.Company.create(self.api, {
            'name': 'MyTestCompany',
            'description': 'A manufacturer *AND* a supplier',
            'is_manufacturer': True,
            'is_supplier': True,
        })

        self.assertIsNotNone(c)

        self.assertEqual(len(c.getManufacturedParts()), 0)
        self.assertEqual(len(c.getSuppliedParts()), 0)

        # Create some 'manufactured parts'
        for i in range(3):

            mpn = f"MPN_XYX-{i}_{c.pk}"
            sku = f"SKU_ABC-{i}_{c.pk}"

            # Create a new ManufacturerPart
            m_part = company.ManufacturerPart.create(self.api, {
                'part': 1,
                'manufacturer': c.pk,
                'MPN': mpn
            })

            # Creating a unique SupplierPart should also create a ManufacturerPart
            company.SupplierPart.create(self.api, {
                'supplier': c.pk,
                'part': 1,
                'manufacturer_part': m_part.pk,
                'SKU': sku,
            })

        self.assertEqual(len(c.getManufacturedParts()), 3)
        self.assertEqual(len(c.getSuppliedParts()), 3)

    def test_manufacturer_part_create(self):
        manufacturer = company.Company(self.api, 1)

        manufacturer_part = company.ManufacturerPart(self.api, {
            'manufacturer': manufacturer,
            'MPN': 'MPN_TEST',
        })

        self.assertIsNotNone(manufacturer_part)

    def test_manufacturer_part_parameters(self):
        """
        Test that we can create, retrieve and edit ManufacturerPartParameter objects
        """

        n = len(company.ManufacturerPart.list(self.api))

        mpn = f"XYZ-12345678-{n}"

        # First, create a new ManufacturerPart
        part = company.ManufacturerPart.create(self.api, {
            'manufacturer': 1,
            'part': 1,
            'MPN': mpn,
        })

        self.assertIsNotNone(part)
        self.assertEqual(len(company.ManufacturerPart.list(self.api)), n + 1)

        # Part should (initially) not have any parameters
        self.assertEqual(len(part.getParameters()), 0)

        # Now, let's create some!
        for idx in range(10):

            parameter = company.ManufacturerPartParameter.create(self.api, {
                'manufacturer_part': part.pk,
                'name': f"param {idx}",
                'value': f"{idx}",
            })

            self.assertIsNotNone(parameter)

        # Now should have 10 unique parameters
        self.assertEqual(len(part.getParameters()), 10)

        # Attempt to create a duplicate parameter
        parameter = company.ManufacturerPartParameter.create(self.api, {
            'manufacturer_part': part.pk,
            'name': 'param 0',
            'value': 'some value',
        })

        self.assertIsNone(parameter)
        self.assertEqual(len(part.getParameters()), 10)

        # Test that we can edit a ManufacturerPartParameter
        parameter = part.getParameters()[0]

        self.assertEqual(parameter.value, '0')

        parameter['value'] = 'new value'
        parameter.save()

        self.assertEqual(parameter.value, 'new value')

        parameter['value'] = 'dummy value'
        parameter.reload()

        self.assertEqual(parameter.value, 'new value')

        # Test that the "list" function works correctly
        results = company.ManufacturerPartParameter.list(self.api)
        self.assertGreaterEqual(len(results), 10)

        results = company.ManufacturerPartParameter.list(self.api, name='param 1')
        self.assertGreaterEqual(len(results), 1)

        results = company.ManufacturerPartParameter.list(self.api, manufacturer_part=part.pk)
        self.assertGreaterEqual(len(results), 10)

    def test_supplier_part_create(self):
        """
        Test that we can create SupplierPart objects via the API
        """

        supplier = company.Company(self.api, 1)

        supplier_part = company.SupplierPart(self.api, {
            'manufacturer': supplier,
            'SKU': 'SKU_TEST',
        })

        self.assertIsNotNone(supplier_part)
