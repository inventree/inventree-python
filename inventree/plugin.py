# -*- coding: utf-8 -*-

import inventree.base


class InvenTreePlugin(inventree.base.MetadataMixin, inventree.base.InventreeObject):
    """Represents a PluginConfig instance on the InvenTree server."""

    URL = 'plugins'
    MIN_API_VERSION = 197

    @classmethod
    def getPkField(cls):
        """Return the primary key field for the PluginConfig object."""
        return 'key'

    def setActive(self, active: bool):
        """Activate or deactivate this plugin."""

        url = f'plugins/{self.pk}/activate/'

        self._api.post(url, data={'active': active})
