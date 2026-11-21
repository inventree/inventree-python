# -*- coding: utf-8 -*-
"""Pricing models.

Ref: https://github.com/inventree/InvenTree/pull/13034
"""

import inventree.base


class PricingModelMixin:
    """Mixin class for models whose API endpoints moved to the 'pricing' app.

    - For servers with API version >= PRICING_API_VERSION, the new URL is used
    - For older servers, the LEGACY_URL is used
    """

    # API version at which pricing endpoints moved from /api/part/ to /api/pricing/
    PRICING_API_VERSION = 562

    # URL for the endpoint on older servers
    LEGACY_URL = ""

    @classmethod
    def useLegacyUrl(cls, api=None):
        """Return True if the server requires the legacy (pre-pricing app) URL.

        If the API version is unknown, the new URL is assumed.
        """

        api_version = getattr(api, 'api_version', None)

        return api_version is not None and api_version < cls.PRICING_API_VERSION

    @classmethod
    def get_url(cls, api=None):
        """Return the URL for this model, based on the server API version."""

        if cls.useLegacyUrl(api):
            url = cls.LEGACY_URL

            if not url.endswith('/'):
                url += '/'

            return url

        return super().get_url(api)


class InternalPrice(inventree.base.AuditLogMixin, PricingModelMixin, inventree.base.InventreeObject):
    """ Class representing the InternalPrice model """

    URL = 'pricing/internal-price/'
    MODEL_TYPE = 'partinternalpricebreak'
    LEGACY_URL = 'part/internal-price/'

    @classmethod
    def setInternalPrice(cls, api, part, quantity: int, price: float):
        """
        Set the internal price for this part
        """

        data = {
            'part': part,
            'quantity': quantity,
            'price': price,
        }

        # Send the data to the server
        return api.post(cls.get_url(api), data)


class SalePrice(inventree.base.AuditLogMixin, PricingModelMixin, inventree.base.InventreeObject):
    """ Class representing the SalePrice model """

    URL = 'pricing/sale-price/'
    MODEL_TYPE = 'partsellpricebreak'
    LEGACY_URL = 'part/sale-price/'

    @classmethod
    def setSalePrice(cls, api, part, quantity: int, price: float, price_currency: str):
        """
        Set the sale price for this part
        """

        data = {
            'part': part,
            'quantity': quantity,
            'price': price,
            'price_currency': price_currency,
        }

        # Send the data to the server
        return api.post(cls.get_url(api), data)


class PartPricing(PricingModelMixin, inventree.base.InventreeObject):
    """Class representing the cached pricing data for a particular Part.

    Unlike other models, this is accessed via the primary key of the linked Part:

    - API version >= 561: pricing/part/<part>/
    - Older API versions: part/<part>/pricing/

    There is no list endpoint, and pricing data cannot be created or deleted.
    Writable fields (e.g. override_min, override_max) can be changed via save().
    """

    URL = 'pricing/part/'
    LEGACY_URL = 'part/'

    def __init__(self, api, part, data=None):
        """Instantiate the PartPricing object for a given Part.

        Args:
            api - The request manager object
            part - The Part instance (or primary key value) to which this pricing data belongs
            data - JSON representation of the pricing data
        """

        self.checkApiVersion(api)

        part = getattr(part, 'pk', part)

        try:
            part = int(str(part).strip())
        except Exception:
            raise TypeError(f"Invalid part value '{part}' for {self.__class__}")

        if part <= 0:
            raise ValueError(f"Supplied part value ({part}) for {self.__class__} must be positive.")

        self._part = part
        self._url = self.get_detail_url(api, part)
        self._api = api

        if data is None:
            data = {}

        self._data = data

        # If the data are not populated, fetch from server
        if len(self._data) == 0:
            self.reload()

    @classmethod
    def get_detail_url(cls, api, part: int):
        """Return the pricing URL for the given Part, based on the server API version."""

        if cls.useLegacyUrl(api):
            return f"{cls.LEGACY_URL}{part}/pricing/"

        return f"{cls.URL}{part}/"

    @classmethod
    def getPkField(cls):
        """Pricing data is identified by the linked Part."""
        return 'part'

    def getPkValue(self):
        """Return the primary key of the linked Part."""
        return self._part

    def updatePricing(self):
        """Request that the server recalculate pricing data for this part.

        Note: The server may perform the update in the background,
        in which case the returned data may not yet reflect the new pricing.
        """

        return self.save(data={'update': True})

    @classmethod
    def _unsupported(cls, action):
        raise NotImplementedError(f"'{action}' is not supported for {cls.__name__} - use Part.getPricing() instead")

    @classmethod
    def options(cls, api):
        cls._unsupported('options')

    @classmethod
    def create(cls, api, data, **kwargs):
        cls._unsupported('create')

    @classmethod
    def count(cls, api, **kwargs):
        cls._unsupported('count')

    @classmethod
    def list(cls, api, **kwargs):
        cls._unsupported('list')

    def delete(self):
        self._unsupported('delete')


# API version which introduced the StockItemCostEntry and StockItemCost models,
# and removed the StockItem 'purchase_price' field.
# Ref: https://github.com/inventree/InvenTree/pull/13294
STOCK_COST_API_VERSION = 583


class CostType:
    """Category of a StockItemCostEntry - i.e. *what* the cost is for.

    Values match the server-side 'CostType' status codes.
    The server provides the (translated) labels via StockItemCostEntry.getCostTypes()
    """

    PURCHASE = 10
    LANDED = 20
    FEES = 30
    MATERIAL = 40
    MANUFACTURING = 50
    ADJUSTMENT = 60
    OTHER = 90


class StockItemCostEntry(inventree.base.AuditLogMixin, inventree.base.InventreeObject):
    """Class representing a single cost entry against a StockItem.

    A StockItem may have any number of cost entries, which are summed
    (in the default currency) to produce the StockItemCost summary.

    Notes:
        - All costs are *per unit* of the stock item
        - Provide 'min_cost' and / or 'max_cost' - if only one is provided, the server sets the other to match
        - Accessing cost entries requires both the 'pricing' and 'stock' roles
          (view to read, change to write)

    Ref: https://github.com/inventree/InvenTree/pull/13294
    """

    URL = 'pricing/stock-cost-entry/'
    MODEL_TYPE = 'stockitemcostentry'
    MIN_API_VERSION = STOCK_COST_API_VERSION

    @classmethod
    def addCost(cls, api, stock_item, cost_type=CostType.PURCHASE, cost=None, min_cost=None, max_cost=None, currency=None, **kwargs):
        """Create a new cost entry against a StockItem.

        Arguments:
            api: InvenTreeAPI instance
            stock_item: StockItem instance or primary key
            cost_type: Category of the cost (see CostType)
            cost: A single unit cost - shorthand for min_cost = max_cost = cost
            min_cost: Minimum unit cost
            max_cost: Maximum unit cost
            currency: Currency code (defaults to the server default currency)
            kwargs: Any other fields (e.g. 'notes', 'source', 'source_data')

        Returns:
            The created StockItemCostEntry instance

        Raises:
            ValueError: If no cost is provided, or both 'cost' and 'min_cost' / 'max_cost' are provided
            NotImplementedError: If the server API version is too old
        """

        if cost is not None:
            if min_cost is not None or max_cost is not None:
                raise ValueError("Provide either 'cost', or 'min_cost' / 'max_cost'")

            min_cost = max_cost = cost

        if min_cost is None and max_cost is None:
            raise ValueError("A cost value must be provided")

        data = {
            **kwargs,
            'stock_item': getattr(stock_item, 'pk', stock_item),
            'cost_type': int(cost_type),
        }

        if min_cost is not None:
            data['min_cost'] = min_cost

        if max_cost is not None:
            data['max_cost'] = max_cost

        if currency:
            data['currency'] = currency

        return cls.create(api, data)

    @classmethod
    def getCostTypes(cls, api):
        """Return the cost type definitions provided by the server."""

        cls.checkApiVersion(api)

        return api.get(f"{cls.get_url(api)}status/")

    def getStockItem(self):
        """Return the StockItem associated with this cost entry."""

        from inventree.stock import StockItem

        return StockItem(self._api, pk=self.stock_item)


class StockItemCost(inventree.base.InventreeObject):
    """Class representing the (read-only) cost summary for a StockItem.

    The summary is calculated by the server from the StockItemCostEntry records
    for the stock item, and cannot be created, edited or deleted directly.

    Notes:
        - The summary 'pk' is not the same as the StockItem 'pk' - use StockItem.getCost()
        - 'min_cost' / 'max_cost' are the total unit cost, in the server default 'currency'
        - 'incomplete' is True if any cost entry could not be included (e.g. no exchange rate available)

    Ref: https://github.com/inventree/InvenTree/pull/13294
    """

    URL = 'pricing/stock-cost/'
    MODEL_TYPE = 'stockitemcost'
    MIN_API_VERSION = STOCK_COST_API_VERSION

    @classmethod
    def forStockItem(cls, api, stock_item):
        """Return the cost summary for a StockItem, or None if it has no cost data.

        Arguments:
            api: InvenTreeAPI instance
            stock_item: StockItem instance or primary key
        """

        results = cls.list(api, stock_item=getattr(stock_item, 'pk', stock_item))

        return results[0] if results else None

    def getStockItem(self):
        """Return the StockItem associated with this cost summary."""

        from inventree.stock import StockItem

        return StockItem(self._api, pk=self.stock_item)

    @classmethod
    def _unsupported(cls, action):
        raise NotImplementedError(f"'{action}' is not supported for {cls.__name__} - the cost summary is read-only (use StockItemCostEntry instead)")

    @classmethod
    def create(cls, api, data, **kwargs):
        cls._unsupported('create')

    def save(self, data=None, files=None, method='PATCH'):
        self._unsupported('save')

    def delete(self):
        self._unsupported('delete')
