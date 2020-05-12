# -*- coding: utf-8 -*-

"""
A simple script to test connection to an InvenTree server.
User must provide address / username / password information.
"""

import argparse
import logging
import sys

from inventree.api import InvenTreeAPI
from inventree.base import INVENTREE_PYTHON_VERSION


def test_server(address, **kwargs):
    """
    Perform basic server checks.
    """

    if kwargs.get('debug', False):
        # Print all debug messages
        logging.basicConfig(level=logging.INFO)

    api = InvenTreeAPI(address, **kwargs)

    assert api.server_details is not None
    assert api.token is not None

    print("Server Details:", api.server_details)
    print("Token:", api.token)

    print("All checks passed OK...")


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description="InvenTree server test")

    parser.add_argument("address", help="InvenTree server address")
    parser.add_argument("-u", "--username", help="Username", default=None)
    parser.add_argument("-p", "--password", help="Password", default=None)
    parser.add_argument("-t", "--token", help="Authentication token", default=None)

    args = parser.parse_args()

    print("InvenTree python version: " + INVENTREE_PYTHON_VERSION)

    # User must provide either USERNAME/PASSWORD or Token
    if args.token is None:
        if args.username is None:
            logging.error("Username must be provided")
            sys.exit(1)
        
        if args.password is None:
            logging.error("Password must be provided")
            sys.exit(1)

    test_server(
        args.address,
        username=args.username,
        password=args.password,
        token=args.token
    )
