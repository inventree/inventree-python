# -*- coding: utf-8 -*-

from inventree import api

SERVER = "http://127.0.0.1:8000"
USERNAME = "admin"
PASSWORD = "password"

API = api.InvenTreeAPI(SERVER, username=USERNAME, password=PASSWORD)

# Ensure that we connected to the server
assert API.token is not None
assert API.server_details is not None

assert 'server' in API.server_details.keys()
assert 'instance' in API.server_details.keys()

assert API.server_details['server'] == 'InvenTree'
