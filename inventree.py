import requests
from requests.auth import HTTPBasicAuth
import os
import json


class InventreeRequest(object):

    def __init__(self, base_url, **kwargs):
        """ Initialize class with initial parameters

        Args:
            base_url - Base API URL
            
        kwargs:
            username - Login username
            password - Login password

        """

        self.base_url = base_url

        self.username = kwargs.get('username', None)
        self.password = kwargs.get('password', None)

        if self.username and self.password:
            self.auth = HTTPBasicAuth(self.username, self.password)
        else:
            self.auth = None

    def get(self, url, **kwargs):
        """ Perform a GET request

        Args:
            url - API url

        kwargs:

        """

        print(os.path.join(self.base_url, url))

        response = requests.get(os.path.join(self.base_url, url), auth=self.auth)

        try:
            data = json.loads(response.text)
        except json.decoder.JSONDecodeError:
            print("Error decoding JSON response")
            print(response)
            print(response.text)
            return None

        return data