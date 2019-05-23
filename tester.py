from inventree_api import InvenTreeAPI
from inventree_object import Part, BomItem

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
