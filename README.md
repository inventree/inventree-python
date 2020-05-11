
[![PyPi version](https://pypip.in/v/inventree/badge.png)](https://pypi.org/project/inventree/) [![Build Status](https://travis-ci.org/inventree/inventree-python.svg?branch=master)](https://travis-ci.org/inventree/inventree-python)

## InvenTree Python Interface

Python library for communication with the [InvenTree parts management system](https:///github.com/inventree/inventree) using the integrated REST API.

This library provides a class-based interface for interacting with the database. Each database table is represented as a class object which provides features analogous to the REST CRUD endpoints (Create, Retrieve, Update, Destroy).

## Installation

The InvenTree python library can be easily installed using PIP:

`pip install inventree`

## Example Usage

Very little code is required to start using the Python InvenTree interface.

A minimal example to list all the BOM items required to make a Part is as follows:

```python
from inventree.api import InvenTreeAPI
from inventree.part import Part, BomItem
from inventree.company import SupplierPart

MY_USERNAME = 'not_my_real_username'
MY_PASSWORD = 'not_my_real_password'

api = InvenTreeAPI('http://127.0.0.1:8000/api/', username=MY_USERNAME, password=MY_PASSWORD)

# Access a single part, and get its BOM items directly
part = Part(api, pk=10)
bom_items = part.get_bom_items()

# Alternatively, BOM items can be requested directly from the database
bom_items = BomItem.list(api, part=10)

# Each request is returned as a class object which can be queried further
# Extract all pricing information available for each supplier part for each BOM Item
for item in bom_items:
    supplier_part = SupplierPart.list(api, part=item['sub_part'])

    for part in supplier_parts:
        price_breaks = part.get_price_breaks()
        
        for pb in price_break:
            print(' - ${price} @ {q}'.format(price=pb['cost'], q=pb['quantity']))
```
