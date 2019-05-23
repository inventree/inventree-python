from inventree_api import InvenTreeAPI
from inventree_object import Part, PartCategory, StockLocation, BomItem

""" User will need to provide a file called 'inventree_credentials.py'

which contains:

INVENTREE_URL e.g. 'http://127.0.0.1:8000/api/'
INVENTREE_USERNAME e.g. 'my_username'
INVENTREE_PASSWORD e.g. 'my_password'
"""

from inventree_credentials import INVENTREE_URL, INVENTREE_USERNAME, INVENTREE_PASSWORD

api = InvenTreeAPI(INVENTREE_URL,
                   username=INVENTREE_USERNAME,
                   password=INVENTREE_PASSWORD)

# List part categories
print("\nPart Categories:")
for category in PartCategory.list(api):

    parts = category.get_parts()

    print(category['name'], '-', len(parts), 'parts')

# List stock locations

print("\nStock Items:")
for location in StockLocation.list(api):

    items = location.get_stock_items()

    print(location['name'], '-', len(items), 'items')