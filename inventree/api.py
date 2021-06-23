# -*- coding: utf-8 -*-

"""
The inventree_api module handles low level requests and authentication
with the InvenTree database server.
"""


import requests
from requests.auth import HTTPBasicAuth
import os
import json
import logging


logger = logging.getLogger('inventree')


class InvenTreeAPI(object):
    """
    Basic class for performing Inventree API requests.
    """

    MIN_SUPPORTED_API_VERSION = 6

    @staticmethod
    def getMinApiVersion():
        """
        Return the minimum supported API version
        """

        return InvenTreeAPI.MIN_SUPPORTED_API_VERSION

    def __init__(self, base_url, **kwargs):
        """ Initialize class with initial parameters

        Args:
            base_url - Base API URL
            
        kwargs:
            username - Login username
            password - Login password
            token - Authentication token (if provided, username/password are ignored)
            use_token_auth - Use token authentication? (default = True)
            verbose - Print extra debug messages (default = False)
        """

        if not base_url.endswith('/'):
            base_url += '/'

        # Server address *must* end with /api/
        if not base_url.endswith('/api/'):
            base_url = os.path.join(base_url, 'api')

        if not base_url.endswith('/'):
            base_url += '/'

        self.base_url = base_url

        logger.info("Connecting to server: " + str(self.base_url))

        self.username = kwargs.get('username', None)
        self.password = kwargs.get('password', None)
        self.token = kwargs.get('token', None)
        self.use_token_auth = kwargs.get('use_token_auth', True)
        self.verbose = kwargs.get('verbose', False)

        # Check if the server is there
        if not self.testServer():
            raise ConnectionRefusedError("Could not connect to InvenTree server")

        # Basic authentication
        self.auth = HTTPBasicAuth(self.username, self.password)
        
        if self.use_token_auth:
            if not self.token:
                self.requestToken()

    def clean_url(self, url):

        url = os.path.join(self.base_url, url)

        if not url.endswith('/'):
            url += '/'

        return url

    def testServer(self):
        """
        Check to see if the server is present.
        The InvenTree server provides a simple endpoint at /api/
        which contains some simple data (and does not require authentication)
        """

        self.server_details = None

        logger.info("Checking InvenTree server connection...")

        try:
            response = requests.get(self.base_url)
        except requests.exceptions.ConnectionError:
            logger.error("Server connection refused - check server address")
            return False

        if not response.status_code == 200:
            logger.error("Error code from server: {code} - {detail}".format(
                code=response.status_code,
                detail=response.text
            ))

            return False

        # Record server details
        self.server_details = json.loads(response.text)

        logger.info("InvenTree server details: " + str(response.text))

        # The details provided by the server should include some specific data:
        server_name = str(self.server_details.get('server', ''))

        if not server_name.lower() == 'inventree':
            logger.warning("Server returned strange response (expected 'InvenTree', found '{name}')".format(
                name=server_name
            ))

        api_version = self.server_details.get('apiVersion', '1')

        try:
            api_version = int(api_version)
        except ValueError:
            raise ValueError(f"Server returned invalid API version: '{api_version}'")

        if api_version < InvenTreeAPI.getMinApiVersion():
            raise ValueError(f"Server API version ({api_version}) is older than minimum supported API version ({InvenTreeAPI.getMinApiVersion()})")

        return True

    def requestToken(self):
        """ Return authentication token from the server """

        if not self.username or not self.password:
            raise AttributeError('Supply username and password to request token')

        logger.info("Requesting auth token from server...")

        # Request an auth token from the server
        token_url = os.path.join(self.base_url, 'user/token/')
        
        reply = requests.get(token_url, auth=self.auth)

        data = json.loads(reply.text)

        if not reply.status_code == 200:
            logger.error("Error requesting token: {code} - {detail}".format(
                code=reply.status_code,
                detail=str(reply.text)
            ))
            return None

        if 'token' not in data.keys():
            logger.error("Token not returned by server: {detail}".format(
                detail=str(reply.text)
            ))
            return None

        self.token = json.loads(reply.text)['token']

        logger.info("Authentication token: " + self.token)

        return self.token

    def request(self, url, **kwargs):
        """ Perform a URL request to the Inventree API """

        # Remove leading slash
        if url.startswith('/'):
            url = url[1:]

        api_url = os.path.join(self.base_url, url)

        if not api_url.endswith('/'):
            api_url += '/'

        method = kwargs.get('method', 'get')

        params = kwargs.get('params', {})

        json = kwargs.get('json', {})

        files = kwargs.get('files', {})

        headers = kwargs.get('headers', {})

        search_term = kwargs.get('search', None)

        if search_term is not None:
            params['search'] = search_term

        methods = {
            'GET': requests.get,
            'POST': requests.post,
            'PUT': requests.put,
            'PATCH': requests.patch,
            'DELETE': requests.delete,
            'OPTIONS': requests.options,
        }

        if method.upper() not in methods.keys():
            logger.error("Unknown request method '{m}'".format(m=method))
            return None

        method = method.upper()

        if self.use_token_auth and self.token:
            headers['AUTHORIZATION'] = 'Token {t}'.format(t=self.token)
            auth = None
        else:
            auth = self.auth

        logger.debug("Sending Request:")
        logger.debug(" - URL:", method, api_url)
        logger.debug(" - auth:", auth)
        logger.debug(" - params:", params)
        logger.debug(" - headers:", headers)
        logger.debug(" - json:", json)
        logger.debug(" - files:", files)

        try:
            response = methods[method](
                api_url,
                auth=auth,
                params=params,
                headers=headers,
                json=json,
                files=files
            )

        except requests.exceptions.ConnectionError:
            logger.error("Connection refused - '{url}'".format(url=api_url))
            return None

        if response is None:
            logger.error("Null response - {method} '{url}'".format(method=method, url=api_url))
            return None

        logger.info("Request: {method} {url} - {response}".format(method=method, url=api_url, response=response.status_code))

        # Detect invalid response codes
        # Anything 300+ is 'bad'
        if response.status_code >= 300:
            logger.warning("Bad response ({code}) - {method} '{url}' - {detail}".format(
                code=response.status_code, method=method, url=api_url,
                detail=str(response.text)
            ))

        # A delete request won't return JSON formatted data (ignore further checks)
        if method == 'DELETE':
            return response

        ctype = response.headers.get('content-type')

        if not ctype == 'application/json':
            logger.error("'Response content-type is not JSON - '{url}' - '{f}'".format(url=api_url, f=ctype))
            return None

        return response

    def delete(self, url, **kwargs):
        """ Perform a DELETE request. Used to remove a record in the database.

        """

        headers = kwargs.get('headers', {})

        response = self.request(url, method='delete', headers=headers, **kwargs)

        if response is None:
            return None

        if response.status_code not in [204]:
            logger.error(f"DELETE request failed at '{url}' - {response.status_code}")

        logger.debug(response.status_code, response.text)

        return response

    def post(self, url, data, files=None, **kwargs):
        """ Perform a POST request. Used to create a new record in the database.

        Args:
            url - API endpoint URL
            data - JSON data to create new object
            files - Dict of file attachments
        """

        url = self.clean_url(url)

        headers = kwargs.get('headers', {})

        if self.use_token_auth and self.token:
            headers['AUTHORIZATION'] = 'Token {t}'.format(t=self.token)
            auth = None
        else:
            auth = self.auth

        response = requests.post(url, data=data, headers=headers, auth=auth, files=files, **kwargs)

        if response is None:
            return None

        if response.status_code not in [200, 201]:
            logger.error("POST request failed at '{url}' - {status}".format(url=url, status=response.status_code))
            logger.error(response.text)
            return None
        
        try:
            data = json.loads(response.text)
        except json.decoder.JSONDecodeError:
            logger.error("Error decoding JSON response - '{url}'".format(url=url))
            return None

        return data

    def patch(self, url, data, files=None, **kwargs):
        """
        Perform a PATCH request.

        Args:
            url - API endpoint URL
            data - JSON data
            files - optional FILES struct
        """

        headers = kwargs.get('headers', {})

        params = {
            'format': 'json',
        }

        response = self.request(
            url,
            json=data,
            method='patch',
            headers=headers,
            params=params,
            files=files,
            **kwargs
        )

        if response is None:
            logger.error(f"PATCH returned null response at '{url}'")
            return None

        if response.status_code not in [200, 201]:
            logger.error(f"PATCH request failed at '{url}' - {response.status_code}")
            return None

        try:
            data = json.loads(response.text)
        except json.decoder.JSONDecodeError:
            logger.error(f"Error decoding JSON response - '{url}'")
            return None

        return data

    def put(self, url, data, files=None, **kwargs):
        """
        Perform a PUT request. Used to update existing records in the database.

        Args:
            url - API endpoint URL
            data - JSON data to PUT
        """

        headers = kwargs.get('headers', {})

        params = {
            'format': 'json',
        }

        response = self.request(
            url,
            json=data,
            method='put',
            headers=headers,
            params=params,
            files=files,
            **kwargs
        )

        if response is None:
            return None

        if response.status_code not in [200, 201]:
            logger.error(f"PUT request failed at '{url}' - {response.status_code}")
            return None

        try:
            data = json.loads(response.text)
        except json.decoder.JSONDecodeError:
            logger.error(f"Error decoding JSON response - '{url}'")
            return None

        return data

    def get(self, url, **kwargs):
        """ Perform a GET request

        Args:
            url - API url

        kwargs:

        """

        response = self.request(url, method='get', **kwargs)

        # No response returned
        if response is None:
            return None

        try:
            data = json.loads(response.text)
        except json.decoder.JSONDecodeError:
            logger.error("Error decoding JSON response - '{url}'".format(url=url))
            return None

        return data
