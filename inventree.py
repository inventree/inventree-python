import requests
from requests.auth import HTTPBasicAuth
import os
import json
import logging


class InventreeRequester(object):
    """ Basic class for performing Inventree API requests.

    GET - Fetch data from the server

    """ 

    def __init__(self, base_url, **kwargs):
        """ Initialize class with initial parameters

        Args:
            base_url - Base API URL
            
        kwargs:
            username - Login username (required)
            password - Login password (required)

        """

        self.base_url = base_url

        self.username = kwargs.get('username', None)
        self.password = kwargs.get('password', None)

        if self.username and self.password:
            self.auth = HTTPBasicAuth(self.username, self.password)
        else:
            # TODO - Raise an exception if authentication not provided
            self.auth = None

    def request(self, url, **kwargs):
        """ Perform a URL request to the Inventree API """

        api_url = os.path.join(self.base_url, url)

        method = kwargs.get('method', 'get')

        params = kwargs.get('params', {})

        search_term = kwargs.get('search', None)

        if search_term is not None:
            params['search'] = search_term

        methods = {
            'GET': requests.get,
            'POST': requests.post,
            'PUT': requests.put,
            'DELETE': requests.delete,
        }

        if method.upper() not in methods.keys():
            logging.error("Unknown request method '{m}'".format(m=method))
            return None

        method = method.upper()

        try:
            response = methods[method](api_url, auth=self.auth, params=params)
        except requests.exceptions.ConnectionError:
            logging.error("Connection refused - '{url}'".format(url=api_url))
            return None

        logging.info("Request: {method} {url} - {response}".format(method=method, url=api_url, response=response.status_code))

        # Detect invalid response codes
        # Anything 300+ is 'bad'
        if response.status_code >= 300:
            logging.warning("Bad response ({code}) - '{url}'".format(code=response.status_code, url=api_url))

        ctype = response.headers.get('content-type')

        if not ctype == 'application/json':
            logging.error("'Response content-type is not JSON - '{url}' - '{f}'".format(url=api_url, f=ctype))
            return None

        return response

    def get(self, url, **kwargs):
        """ Perform a GET request

        Args:
            url - API url

        kwargs:

        """

        response = self.request(url, method='get', **kwargs)

        # No response returned 
        if response is None:
            logging.error("No response received - '{url}'".format(url=url))
            return None

        try:
            data = json.loads(response.text)
        except json.decoder.JSONDecodeError:
            logging.error("Error decoding JSON response - '{url}'".format(url=url))
            return None

        return data

    def get_part_list(self, **kwargs):
        """ Return a list of parts with the following optional filters:
        
        Args:
            category - Filter by part category ID
            buildable - Can this part be built from other parts?
            purchaseable - Can this part be purcahsed from suppliers?
        """

        params = {
        }

        for arg in ['category', 'buildable', 'purchaseable']:
            if kwargs.get(arg, None):
                params[arg] = kwargs[arg]

        return self.get('part/', **kwargs)

    def get_part(self, pk, **kwargs):
        """ Return detail of a specific part. Part ID <pk> must be provided """

        response = self.get('part/{pk}/'.format(pk=pk), **kwargs)

        return response

    def get_supplier_part_list(self, **kwargs):
        """ Return a list of supplier part, with the following optional filters:

        Args:
            part - Filter by base part ID
            supplier - Filter by supplier ID
        """

        params = {}

        for arg in ['part', 'supplier']:
            if kwargs.get(arg, None):
                params[arg] = kwargs[arg]

        response = self.get('company/part/', params=params, **kwargs)

        return response

    def get_supplier_part(self, pk, **kwargs):
        """ Return detail of a single supplier part """

        response = self.get('company/part/{pk}/'.format(pk=pk), **kwargs)

        return response

    def get_price_break_list(self, **kwargs):
        """ Return a list of supplier price breaks, with the following optional filters:

        Args:
            part - Filter by supplier part ID
        """

        params = {}

        for arg in ['part']:
            if kwargs.get(arg, None):
                params[arg] = kwargs[arg]

        response = self.get('company/price-break/', params=params, **kwargs)

        return response