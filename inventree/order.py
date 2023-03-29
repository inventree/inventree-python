"""
This file serves a a 'proxy' for various order models,
but the source for these models has now been moved into separate files
"""

# Pass PurchaseOrder models through
from inventree.purchase_order import PurchaseOrder, PurchaseOrderAttachment, PurchaseOrderExtraLineItem, PurchaseOrderLineItem

# Pass SalesOrder models through
from inventree.sales_order import SalesOrder, SalesOrderAttachment, SalesOrderExtraLineItem, SalesOrderLineItem, SalesOrderShipment

# Pass ReturnOrder models through
from inventree.return_order import ReturnOrder, ReturnOrderAttachment, ReturnOrderExtraLineItem, ReturnOrderLineItem
