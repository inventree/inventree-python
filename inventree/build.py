# -*- coding: utf-8 -*-

from inventree import base


class Build(base.InventreeObject):
    """ Class representing the Build database model """

    URL = 'build'
    FILTERS = ['part']
