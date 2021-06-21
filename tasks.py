# -*- coding: utf-8 -*-

try:
    from invoke import ctask as task
except ImportError:
    from invoke import task

import os


@task
def style(c):
    """
    Run PEP style checks against the codebase
    """

    print("Running PEP code style checks...")
    c.run('flake8 .')


@task
def test(c, server="http://127.0.0.1:8000", username="admin", password="password"):
    """
    Perform unit testing against an InvenTree server
    """

    print("Running unit tests...")

    # Set environment variables so test scripts can access them
    os.environ['INVENTREE_PYTHON_TEST_SERVER'] = server
    os.environ['INVENTREE_PYTHON_TEST_USERNAME'] = username
    os.environ['INVENTREE_PYTHON_TEST_PASSWORD'] = password

    c.run('coverage run -m unittest discover -s test/')
