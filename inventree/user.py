# -*- coding: utf-8 -*-

import logging

import inventree.base

logger = logging.getLogger('inventree')


class User(inventree.base.InventreeObject):
    """ Class representing the User database model """

    URL = 'user'
