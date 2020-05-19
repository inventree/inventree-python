# -*- coding: utf-8 -*-

from inventree import api
from inventree import part
from inventree import stock

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

# Tests for part category interface

# List all category objects
categories = part.PartCategory.list(API)

assert len(categories) == 7

# Get a particular category
electronics = part.PartCategory(API, 1)

# This is a top-level category, should not have a parent!
assert electronics.getParentCategory() is None
assert electronics.name == "Electronics"

children = electronics.getChildCategories()
assert len(children) == 1
passives = children[0]
assert passives.name == "Passives"
children = passives.getChildCategories()
assert len(children) == 3
parent = passives.getParentCategory()
assert parent.pk == 1
assert parent.name == "Electronics"

print(categories)