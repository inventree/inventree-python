from inventree_api import InvenTreeAPI
from inventree_object import *

from inventree_credentials import *

import sys

def exit(msg):
    print(msg)
    sys.exit(1)

api = InvenTreeAPI(
        INVENTREE_URL,
        username=INVENTREE_USERNAME,
        password=INVENTREE_PASSWORD)

part = Part(pk=29, api=api)

boms = part.get_bom_items()

for it in boms:

    supplier_parts = SupplierPart.list(api, part=it['sub_part'])

    print(it['quantity'], 'x', it['sub_part_detail']['full_name'])

    for p in supplier_parts:
        print(' -', p['supplier'], p['SKU'])