# -*- coding: utf-8 -*-

try:
    from invoke import ctask as task
except ImportError:
    from invoke import task

import os
import time

import requests
from requests.auth import HTTPBasicAuth
import sys


@task
def style(c):
    """
    Run PEP style checks against the codebase
    """

    print("Running PEP code style checks...")
    c.run('flake8 .')


@task
def update_image(c, debug=True):
    """
    Update the InvenTree image to the latest version
    """

    print("Pulling latest InvenTree image from docker hub (maybe grab a coffee!)")
    
    c.run("docker-compose -f test/docker-compose.yml pull", hide=None if debug else 'both')

@task
def reset_data(c, debug=False):
    """
    Reset the database to a known state.
    This is achieved by installing the InvenTree test fixture data.
    """
    # Reset the database to a known state
    print("Reset test database to a known state (this might take a little while...)")

    c.run("docker-compose -f test/docker-compose.yml run inventree-py-test-server invoke migrate", hide=None if debug else 'both')
    c.run("docker-compose -f test/docker-compose.yml run inventree-py-test-server invoke import-fixtures", hide=None if debug else 'both')

@task
def check_server(c, host="http://localhost:12345", username="testuser", password="testpassword", debug=True):
    """
    Check that we can ping the sevrer and get a token
    """

    auth = HTTPBasicAuth(username=username, password=password)

    url = f"{host}/api/user/token/"

    response = requests.get(url, auth=auth)

    if response.status_code != 200:
        if debug:
            print(f"Invalid status code: ${response.status_code}")
        return False

    if 'token' not in response.text:
        if debug:
            print(f"Token not in returned response")
        return False

    # We have confirmed that the server is available    
    if debug:
        print(f"InvenTree server is available at {host}")

    return True


@task
def test(c, update=False, reset=True, debug=False):
    """
    Run the unit tests for the python bindings. 
    Performs the following steps:

    - Ensure the docker container is up and running
    - Reset the database to a known state
    - Perform unit testing
    """

    if update:
        # Pull down the latest InvenTree docker image
        update_image(c, debug=debug)

    if reset:
        reset_data(c, debug=debug)
    
    # Start the InvenTree server
    print("Restarting InvenTree server instance")
    c.run('docker-compose -f test/docker-compose.yml up -d', hide='both')

    # Wait until the docker server is running, and API is accessible

    print("Waiting for InvenTree server to response:")

    count = 60

    while not check_server(c, debug=False) and count > 0:
        count -= 1
        time.sleep(1)
    
    if count == 0:
        print("No response from InvenTree server")
        sys.exit(1)
    else:
        print("InvenTree server is active - proceeding with tests")

    # Set environment variables so test scripts can access them
    os.environ['INVENTREE_PYTHON_TEST_SERVER'] = 'http://localhost:12345'
    os.environ['INVENTREE_PYTHON_TEST_USERNAME'] = 'testuser'
    os.environ['INVENTREE_PYTHON_TEST_PASSWORD'] = 'testpassword'

    # Run unit tests
    c.run('coverage run -m unittest discover -s test/')
