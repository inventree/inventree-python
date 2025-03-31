import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from requests_oauthlib import OAuth2Session
import webbrowser
import urllib.parse as urlparse

# Environment setup
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
USABLE_PORT_RANGE = (29170, 292180)


class OAuthClient:
    def __init__(self, server_url: str = "http://localhost:8000", client_id: str ='', scopes: list[str] = None) -> None:
        self.server_url = server_url
        self.client_id = client_id
        self.scopes = scopes if scopes is not None else []

        self._handler_wrapper = RequestHandlerWrapper(self)
        self._setup_callback()
        self._poll_user()
    
    def get_url(self, path: str) -> str:
        """Get the authorization URL."""
        return urlparse.urljoin(self.server_url, path)

    def _setup_callback(self):
        for port in range(*USABLE_PORT_RANGE):
            try:
                self.server = HTTPServer(("127.0.0.1", port), self._handler_wrapper.request_handler)
                self._port = port
                break
            except OSError:
                continue
        else:
            raise Exception("No port found.")

    def _poll_user(self):
        self._session = OAuth2Session(
            self.client_id, scope=self.scopes, redirect_uri=f"http://localhost:{self._port}", pkce="S256"
        )
        auth_url, state = self._session.authorization_url(self.get_url('/o/authorize/'), access_type="offline")
        self._state = state
        webbrowser.open_new_tab(auth_url)

        while not self._handler_wrapper.done:
            self.server.handle_request()
        if self._handler_wrapper.error:
            raise Exception(self._handler_wrapper.error)

    def callback(self, callback_url: str):
        self._session.fetch_token(self.get_url("/o/token/"), authorization_response=callback_url, include_client_id=True)
        self._access_token = self._session.access_token


class RequestHandlerWrapper:
    """Provides callback for OIDC endpint."""
    def __init__(self, oauth_client) -> None:
        self.done = False
        self.error = None
        self.client: OAuthClient = oauth_client

    @property
    def request_handler(self):
        wrapper = self

        class RequestHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                parsed_url = urlparse.urlparse(self.path)
                if parsed_url.path == "/":
                    error = urlparse.parse_qs(parsed_url.query).get("error", [None])[0]
                    if error:
                        wrapper.error = error
                        self.send(200)
                    else:
                        try:
                            wrapper.client.callback(self.path)
                        except OAuthError as e:
                            wrapper.error = e.message
                            self.send(400)
                        else:
                            self.send(200, 'Success! You can close this window.')
                    wrapper.done = True
                else:
                    self.send(404)

            def send(self, status_code, content=None):
                self.send_response(status_code)
                if content:
                    self.wfile.write(content.encode("utf-8"))
                else:
                    self.wfile.write(b"")
                self.send_header("Content-type", "text/html")
                self.end_headers()

            def log_message(self, *args):
                pass  # Suppress logging

        return RequestHandler

class OAuthError(Exception):
    """Exception raised during the OAuth process."""
    def __init__(self, message: str) -> None:
        self.message = message
