"""
This file serves a a 'proxy' for various order models,
but the source for these models has now been moved into separate files
"""

# Pass PurchaseOrder models through
from inventree.purchase_order import PurchaseOrder  # noqa:F401
from inventree.purchase_order import PurchaseOrderAttachment  # noqa:F401
from inventree.purchase_order import PurchaseOrderExtraLineItem  # noqa:F401
from inventree.purchase_order import PurchaseOrderLineItem  # noqa:F401
# Pass ReturnOrder models through
from inventree.return_order import ReturnOrder  # noqa:F401
from inventree.return_order import ReturnOrderAttachment  # noqa:F401
from inventree.return_order import ReturnOrderExtraLineItem  # noqa:F401
from inventree.return_order import ReturnOrderLineItem  # noqa:F401
# Pass SalesOrder models through
from inventree.sales_order import SalesOrder  # noqa:F401
from inventree.sales_order import SalesOrderAttachment  # noqa:F401
from inventree.sales_order import SalesOrderExtraLineItem  # noqa:F401
from inventree.sales_order import SalesOrderLineItem  # noqa:F401
from inventree.sales_order import SalesOrderShipment  # noqa:F401
