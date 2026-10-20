"""
This file serves a a 'proxy' for various order models,
but the source for these models has now been moved into separate files
"""

# Pass PurchaseOrder models through
from inventree.purchase_order import (
    PurchaseOrder,  # noqa:F401
    PurchaseOrderExtraLineItem,  # noqa:F401
    PurchaseOrderLineItem,  # noqa:F401
)

# Pass ReturnOrder models through
from inventree.return_order import (
    ReturnOrder,  # noqa:F401
    ReturnOrderExtraLineItem,  # noqa:F401
    ReturnOrderLineItem,  # noqa:F401
)

# Pass SalesOrder models through
from inventree.sales_order import (
    SalesOrder,  # noqa:F401
    SalesOrderAllocation,  # noqa:F401
    SalesOrderExtraLineItem,  # noqa:F401
    SalesOrderLineItem,  # noqa:F401
    SalesOrderShipment,  # noqa:F401
)
