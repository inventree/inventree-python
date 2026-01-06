# -*- coding: utf-8 -*-

import logging

import inventree.base

logger = logging.getLogger('inventree')


class User(inventree.base.InventreeObject):
    """ Class representing the User database model """

    URL = 'user/'


class Group(inventree.base.InventreeObject):
    """Class representing the Group database model"""

    URL = "user/group/"


class Owner(inventree.base.InventreeObject):
    """Class representing the Owner database model"""

    URL = "user/owner/"
