# -*- coding: utf-8 -*-

import logging

import inventree.base

class InvenTreePlugin(inventree.base.MetadataMixin, inventree.base.InventreeObject):
    """Represents a PluginConfig instance on the InvenTree server."""

    URL = 'plugins'