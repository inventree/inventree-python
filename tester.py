from inventree_api import InvenTreeAPI
from inventree_object import Part, BomItem

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


# List the parts in the database
parts = Part.list(api)

print("Parts:", len(parts))

# List the BOM items in the databse
items = BomItem.list(api)

print("BOM Items:", len(items))
