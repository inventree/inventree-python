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
