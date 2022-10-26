# -*- coding: utf-8 -*-

"""
The inventree_api module handles low level requests and authentication
with the InvenTree database server.
"""

import requests
import os
import json
import logging

from requests.auth import HTTPBasicAuth
from urllib.parse import urljoin, urlparse


logger = logging.getLogger('inventree')


class InvenTreeAPI(object):
    """
    Basic class for performing Inventree API requests.
    """

    MIN_SUPPORTED_API_VERSION = 51

    @staticmethod
    def getMinApiVersion():
        """
        Return the minimum supported API version
        """

        return InvenTreeAPI.MIN_SUPPORTED_API_VERSION

    def __init__(self, host=None, **kwargs):
        """ Initialize class with initial parameters

        Args:
            base_url - Base URL for the InvenTree server, including port (if required)
                       e.g. "http://inventree.server.com:8000"
            
        kwargs:
            username - Login username
            password - Login password
            token - Authentication token (if provided, username/password are ignored)
            use_token_auth - Use token authentication? (default = True)
            verbose - Print extra debug messages (default = False)

        Login details can be specified using environment variables, rather than being provided as arguments:
            INVENTREE_API_HOST - Host address e.g. "http://inventree.server.com:8000"
            INVENTREE_API_USERNAME - Username
            INVENTREE_API_PASSWORD - Password
            INVENTREE_API_TOKEN - User access token
        """

        self.setHostName(host or os.environ.get('INVENTREE_API_HOST', None))

        # Check for environment variables
        self.username = kwargs.get('username', os.environ.get('INVENTREE_API_USERNAME', None))
        self.password = kwargs.get('password', os.environ.get('INVENTREE_API_PASSWORD', None))
        self.token = kwargs.get('token', os.environ.get('INVENTREE_API_TOKEN', None))

        self.use_token_auth = kwargs.get('use_token_auth', True)
        self.verbose = kwargs.get('verbose', False)

        self.auth = None
        self.connected = False

        if kwargs.get('connect', True):
            self.connect()

    def setHostName(self, host):
        """Validate that the provided base URL is valid"""
        
        if host is None:
            raise AttributeError("InvenTreeAPI initialized without providing host address")

        # Ensure that the provided URL is valid
        url = urlparse(host)

        if not url.scheme:
            raise Exception(f"Host '{host}' supplied without valid scheme")
        
        if not url.netloc or not url.hostname:
            raise Exception(f"Host '{host}' supplied without valid hostname")

        # Check if the path is provided with '/api/' at the end
        ps = [el for el in url.path.split('/') if len(el) > 0]

        if len(ps) > 0 and ps[-1] == 'api':
            ps = ps[:-1]

        path = '/'.join(ps)

        # Re-construct the URL as required
        self.base_url = f"{url.scheme}://{url.netloc}/{path}"

        if not self.base_url.endswith('/'):
            self.base_url += '/'

        # Re-construct the API URL as required
        self.api_url = urljoin(self.base_url, 'api/')

    def connect(self):
        """Attempt a connection to the server"""

        logger.info(f"Connecting to server: {self.base_url}")

        self.connected = False

        # Check if the server is there
        if not self.testServer():
            raise ConnectionRefusedError("Could not connect to InvenTree server")

        # Basic authentication
        self.auth = HTTPBasicAuth(self.username, self.password)
        
        if self.use_token_auth:
            if not self.token:
                self.requestToken()
        
        self.connected = True

    def constructApiUrl(self, endpoint_url):
        """Construct an API endpoint URL based on the provided API URL.

        Arguments:
            endpoint_url: The particular API endpoint (everything after "/api/")

        Returns: A fully qualified URL for the subsequent request
        """

        # Strip leading / character if provided
        if endpoint_url.startswith("/"):
            endpoint_url = endpoint_url[1:]

        url = urljoin(self.api_url, endpoint_url)

        # Ensure the API URL ends with a trailing slash
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
            response = requests.get(self.api_url, timeout=2.5)
        except requests.exceptions.ConnectionError as e:
            logger.fatal(f"Server connection error: {str(type(e))}")
            return False
        except Exception as e:
            logger.fatal(f"Unhandled server error: {str(type(e))}")
            # Re-throw the exception
            raise e

        if response.status_code != 200:
            raise requests.exceptions.RequestException(f"Error code from server: {response.status_code} - {response.text}")

        # Record server details
        self.server_details = json.loads(response.text)

        logger.info(f"InvenTree server details: {response.text}")

        # The details provided by the server should include some specific data:
        server_name = str(self.server_details.get('server', ''))

        if not server_name.lower() == 'inventree':
            logger.warning(f"Server returned strange response (expected 'InvenTree', found '{server_name}')")

        api_version = self.server_details.get('apiVersion', '1')

        try:
            api_version = int(api_version)
        except ValueError:
            raise ValueError(f"Server returned invalid API version: '{api_version}'")

        if api_version < InvenTreeAPI.getMinApiVersion():
            raise ValueError(f"Server API version ({api_version}) is older than minimum supported API version ({InvenTreeAPI.getMinApiVersion()})")

        # Store the server API version
        self.api_version = api_version

        return True

    def requestToken(self):
        """ Return authentication token from the server """

        if not self.username or not self.password:
            raise AttributeError('Supply username and password to request token')

        logger.info("Requesting auth token from server...")

        # Request an auth token from the server
        token_url = os.path.join(self.api_url, 'user/token/')
        
        reply = requests.get(token_url, auth=self.auth)

        data = json.loads(reply.text)

        if not reply.status_code == 200:
            logger.error(f"Error requesting token: {reply.status_code} - {reply.text}")
            return None

        if 'token' not in data.keys():
            logger.error(f"Token not returned by server: {reply.text}")
            return None

        self.token = json.loads(reply.text)['token']

        logger.info(f"Authentication token: {self.token}")

        return self.token

    def request(self, api_url, **kwargs):
        """ Perform a URL request to the Inventree API """

        if not self.connected:
            # If we have not established a connection to the server yet, attempt now
            self.connect()

        api_url = self.constructApiUrl(api_url)

        data = kwargs.get('data', kwargs.get('json', {}))
        files = kwargs.get('files', {})
        params = kwargs.get('params', {})
        headers = kwargs.get('headers', {})

        search_term = kwargs.pop('search', None)

        if search_term is not None:
            params['search'] = search_term

        # Use provided HTTP method
        method = kwargs.get('method', 'get')

        methods = {
            'GET': requests.get,
            'POST': requests.post,
            'PUT': requests.put,
            'PATCH': requests.patch,
            'DELETE': requests.delete,
            'OPTIONS': requests.options,
        }

        if method.upper() not in methods.keys():
            logger.error(f"Unknown request method '{method}'")
            return None

        method = method.upper()

        payload = {
            'params': params,
            'timeout': kwargs.get('timeout', 10),
        }

        if self.use_token_auth and self.token:
            headers['AUTHORIZATION'] = f'Token {self.token}'
            auth = None
        else:
            auth = self.auth
        
        payload['headers'] = headers
        payload['auth'] = auth

        # If we are providing files, we cannot upload as a 'json' request
        if files:
            payload['data'] = data
            payload['files'] = files
        else:
            payload['json'] = data

        # Debug request information
        logger.debug("Sending Request:")
        logger.debug(f" - URL: {method} {api_url}")

        for item, value in payload.items():
            logger.debug(f" - {item}: {value}")

        # Send request to server!
        try:
            response = methods[method](api_url, **payload)
        except Exception as e:
            # Re-thrown any caught errors, and add a message to the log
            logger.critical(f"Error at api.request - {method} @ {api_url}")
            raise e

        if response is None:
            logger.error(f"Null response - {method} '{api_url}'")
            return None

        logger.info(f"Request: {method} {api_url} - {response.status_code}")

        # Detect invalid response codes
        # Anything 300+ is 'bad'
        if response.status_code >= 300:

            detail = {
                'detail': 'Error occurred during API request',
                'url': api_url,
                'method': method,
                'status_code': response.status_code,
                'body': response.text,
            }

            if headers:
                detail['headers'] = headers
            
            if params:
                detail['params'] = params
            
            if files:
                detail['files'] = files
            
            if data:
                detail['data'] = data

            raise requests.exceptions.HTTPError(detail)

        # A delete request won't return JSON formatted data (ignore further checks)
        if method == 'DELETE':
            return response

        ctype = response.headers.get('content-type')

        # An API request must respond in JSON format
        if not ctype == 'application/json':
            raise requests.exceptions.InvalidJSONError(
                f"'Response content-type is not JSON - '{api_url}' - '{ctype}'"
            )

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

        logger.debug(f"DELETE request at '{url}' returned: {response.status_code} {response.text}")

        return response

    def post(self, url, data, **kwargs):
        """ Perform a POST request. Used to create a new record in the database.

        Args:
            url - API endpoint URL
            data - JSON data to create new object
            files - Dict of file attachments
        """

        params = {
            'format': kwargs.pop('format', 'json')
        }

        response = self.request(
            url,
            json=data,
            method='post',
            params=params,
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

    def patch(self, url, data, **kwargs):
        """
        Perform a PATCH request.

        Args:
            url - API endpoint URL
            data - JSON data
            files - optional FILES struct
        """

        params = {
            'format': kwargs.pop('format', 'json')
        }

        response = self.request(
            url,
            json=data,
            method='patch',
            params=params,
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

    def put(self, url, data, **kwargs):
        """
        Perform a PUT request. Used to update existing records in the database.

        Args:
            url - API endpoint URL
            data - JSON data to PUT
        """

        params = {
            'format': kwargs.pop('format', 'json')
        }

        response = self.request(
            url,
            json=data,
            method='put',
            params=params,
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
        """ Perform a GET request.

        For argument information, refer to the 'request' method
        """

        response = self.request(url, method='get', **kwargs)

        # No response returned
        if response is None:
            return None

        try:
            data = json.loads(response.text)
        except json.decoder.JSONDecodeError:
            logger.error(f"Error decoding JSON response - '{url}'")
            return None

        return data

    def downloadFile(self, url, destination, overwrite=False):
        """
        Download a file from the InvenTree server.

        Args:
            destination: Filename (string)

        - If the "destination" is a directory, use the filename of the remote URL
        """

        if url.startswith('/'):
            url = url[1:]

        url = urljoin(self.base_url, url)

        if os.path.exists(destination) and os.path.isdir(destination):

            destination = os.path.join(
                destination,
                os.path.basename(url)
            )

        destination = os.path.abspath(destination)

        if os.path.exists(destination) and not overwrite:
            raise FileExistsError(f"Destination file '{destination}' already exists")

        if self.token:
            headers = {
                'AUTHORIZATION': f"Token {self.token}"
            }
            auth = None
        else:
            headers = {}
            auth = self.auth

        with requests.get(url, stream=True, auth=auth, headers=headers) as response:

            # Error code
            if response.status_code >= 300:
                detail = {
                    'detail': 'Error occurred during file download',
                    'url': url,
                    'status_code': response.status_code,
                    'body': response.text
                }

                if headers:
                    detail['headers'] = headers
                
                raise requests.exceptions.HTTPError(detail)

            headers = response.headers

            if 'text/html' in headers['Content-Type']:
                logger.error(f"Error downloading file '{url}': Server return invalid response (text/html)")
                return False

            with open(destination, 'wb') as f:

                for chunk in response.iter_content(chunk_size=16 * 1024):
                    f.write(chunk)

        logger.info(f"Downloaded '{url}' to '{destination}'")
        return True

    def scanBarcode(self, barcode_data):
        """Scan a barcode to see if it matches a known object"""

        response = self.post(
            '/barcode/',
            {
                'barcode': barcode_data,
            }
        )

        return response
