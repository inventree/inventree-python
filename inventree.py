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
            response = methods[method](api_url, auth=self.auth)
        except requests.exceptions.ConnectionError:
            logging.error("Connection refused - '{url}'".format(url=api_url))
            return None

        logging.info("Request: {method} {url} - {response}".format(method=method, url=api_url, response=response.status_code))

        # Detect invalid response codes
        # Anything 300+ is 'bad'
        if response.status_code >= 300:
            logging.warning('Bad response ({code})'.format(code=response.status_code))

        return response

    def get(self, url, **kwargs):
        """ Perform a GET request

        Args:
            url - API url

        kwargs:

        """

        response = self.request(url, method='get')

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
