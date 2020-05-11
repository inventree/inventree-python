# -*- coding: utf-8 -*-

import setuptools

from inventree.base import INVENTREE_PYTHON_VERSION

long_description = "Python interface for InvenTree inventory management system"


setuptools.setup(
    name="inventree",

    version=INVENTREE_PYTHON_VERSION,

    author="Oliver Walters",

    author_email="oliver.henry.walters@gmail.com",

    description="Python interface for InvenTree inventory management system",

    long_description=long_description,

    keywords="bom, bill of materials, stock, inventory, management, barcode",

    url="https://github.com/inventree/inventree-python/",

    license="MIT",

    packages=setuptools.find_packages(),

    install_requires=[
    ],

    python_requires=">=3.6"
)
