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
def reset_data(c, debug=False):
    """
    Reset the database to a known state.
    This is achieved by installing the InvenTree test fixture data.
    """
    # Reset the database to a known state
    print("Reset test database to a known state (this might take a little while...)")

    c.run("docker-compose -f test/docker-compose.yml run inventree-py-test-server invoke migrate", hide=None if debug else 'both')
    c.run("docker-compose -f test/docker-compose.yml run inventree-py-test-server invoke delete-data -f", hide=None if debug else 'both')
    c.run("docker-compose -f test/docker-compose.yml run inventree-py-test-server invoke import-fixtures", hide=None if debug else 'both')


@task(post=[reset_data])
def update_image(c, debug=True):
    """
    Update the InvenTree image to the latest version
    """

    print("Pulling latest InvenTree image from docker hub (maybe grab a coffee!)")
    
    c.run("docker-compose -f test/docker-compose.yml pull", hide=None if debug else 'both')


@task
def check_server(c, host="http://localhost:12345", username="testuser", password="testpassword", debug=True, timeout=30):
    """
    Check that we can ping the sevrer and get a token.
    A generous timeout is applied here, to give the server time to activate
    """

    auth = HTTPBasicAuth(username=username, password=password)

    url = f"{host}/api/user/token/"

    response = None

    while response is None:

        try:
            response = requests.get(url, auth=auth, timeout=0.5)
        except Exception as e:
            if debug:
                print("Error:", str(e))
        
        if response is None:
            timeout -= 1

            time.sleep(1)
        
            if timeout <= 0:
                return False

    if response.status_code != 200:
        if debug:
            print(f"Invalid status code: ${response.status_code}")
        return False

    if 'token' not in response.text:
        if debug:
            print("Token not in returned response:")
            print(str(response.text))
        return False

    # We have confirmed that the server is available
    if debug:
        print(f"InvenTree server is available at {host}")

    return True


@task
def start_server(c, debug=False):
    """
    Launch the InvenTree server (in a docker container)
    """

    # Start the InvenTree server
    print("Starting InvenTree server instance")
    c.run('docker-compose -f test/docker-compose.yml up -d', hide=None if debug else 'both')

    print("Waiting for InvenTree server to respond:")

    count = 60

    while not check_server(c, debug=False) and count > 0:
        count -= 1
        time.sleep(1)
    
    if count == 0:
        print("No response from InvenTree server")
        sys.exit(1)
    else:
        print("InvenTree server is active!")


@task
def stop_server(c, debug=False):
    """
    Stop a running InvenTree test server docker container
    """

    # Stop the server
    c.run('docker-compose -f test/docker-compose.yml down', hide=None if debug else 'both')


@task
def test(c, source=None, update=False, reset=False, debug=False):
    """
    Run the unit tests for the python bindings.
    Performs the following steps:

    - Ensure the docker container is up and running
    - Reset the database to a known state (if --reset flag is given)
    - Perform unit testing
    """

    # If a source file is provided, check that it actually exists
    if source:
        if not os.path.exists(source):
            source = os.path.join('test', source)
        
        if not os.path.exists(source):
            print(f"Error: Source file '{source}' does not exist")
            sys.exit(1)

    if update:
        # Pull down the latest InvenTree docker image
        update_image(c, debug=debug)

    if reset:
        stop_server(c, debug=debug)
        reset_data(c, debug=debug)
    
    # Launch the InvenTree server (dockerized)
    start_server(c)

    # Wait until the docker server is running, and API is accessible

    # Set environment variables so test scripts can access them
    os.environ['INVENTREE_PYTHON_TEST_SERVER'] = 'http://localhost:12345'
    os.environ['INVENTREE_PYTHON_TEST_USERNAME'] = 'testuser'
    os.environ['INVENTREE_PYTHON_TEST_PASSWORD'] = 'testpassword'

    # Run unit tests

    # If a single source file is supplied, test *just* that file
    # Otherwise, test *all* files
    if source:
        print(f"Running tests for '{source}'")
        c.run(f'coverage run -m unittest {source}')
    else:
        # Automatically discover tests, and run only those
        c.run('coverage run -m unittest discover -s test/')
