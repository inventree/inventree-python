
import logging

import inventree.base

logger = logging.getLogger('inventree')


class ProjectCode(inventree.base.InventreeObject):
    """Class representing the 'ProjectCode' database model"""

    URL = 'project-code/'
    REQUIRED_API_VERSION = 109
