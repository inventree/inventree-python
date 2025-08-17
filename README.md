[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PyPI](https://img.shields.io/pypi/v/inventree)](https://pypi.org/project/inventree/)
![Build Status](https://github.com/inventree/inventree-python/actions/workflows/ci.yaml/badge.svg)
[![Coverage Status](https://coveralls.io/repos/github/inventree/inventree-python/badge.svg)](https://coveralls.io/github/inventree/inventree-python)
![PEP](https://github.com/inventree/inventree-python/actions/workflows/pep.yaml/badge.svg)

## InvenTree Python Interface

Python library for communication with the [InvenTree parts management system](https:///github.com/inventree/inventree) using the integrated REST API.

This library provides a class-based interface for interacting with the database. Each database table is represented as a class object which provides features analogous to the REST CRUD endpoints (Create, Retrieve, Update, Destroy).

## Installation

The InvenTree python library can be easily installed using PIP:

```
pip install inventree
```

If you need to rely on system certificates from the OS certificate store instead of the bundled certificates, use

```
pip install inventree[system-certs]
```

This allows pip and Python applications to verify TLS/SSL connections to servers whose certificates are trusted by your system, and can be helpful if you're using a custom certificate authority (CA) for your InvenTree instance's cert.

## Documentation

Refer to the [InvenTree documentation](https://docs.inventree.org/en/latest/api/python/python/)
