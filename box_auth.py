# coding: utf-8

"""
Use the Box OAuth2 strategy to authenticate an application and retrieve its
tokens using a local web server on port 8080.

In the Box developer settings for the application, remember to set
`http://localhost:8080` as the local redirect URI.
"""

from __future__ import print_function, unicode_literals

import bottle
import os
from threading import Thread, Event
import webbrowser
from wsgiref.simple_server import WSGIServer, WSGIRequestHandler, make_server

from boxsdk import OAuth2


def authenticate_to_local_auth_url(client_id, client_secret, oauth_class=OAuth2):
    """
    Use the supplied client ID and secret to retrieve tokens allowing
    Box access for an authorized user.

    :param client_id: The application's Box ID
    :type client_id: str
    :param client_secret: The application's secret string
    :type client_secret: str
    """
    class StoppableWSGIServer(bottle.ServerAdapter):
        def __init__(self, *args, **kwargs):
            super(StoppableWSGIServer, self).__init__(*args, **kwargs)
            self._server = None

        def run(self, app):
            server_cls = self.options.get('server_class', WSGIServer)
            handler_cls = self.options.get('handler_class', WSGIRequestHandler)
            self._server = make_server(self.host, self.port, app, server_cls, handler_cls)
            self._server.serve_forever()

        def stop(self):
            self._server.shutdown()

    auth_code = {}
    auth_code_is_available = Event()

    local_oauth_redirect = bottle.Bottle()

    @local_oauth_redirect.get('/')
    def get_token():
        auth_code['auth_code'] = bottle.request.query.code
        auth_code['state'] = bottle.request.query.state
        auth_code_is_available.set()

    local_server = StoppableWSGIServer(host='localhost', port=8080)
    server_thread = Thread(target=lambda: local_oauth_redirect.run(server=local_server))
    server_thread.start()

    oauth = oauth_class(
        client_id=client_id,
        client_secret=client_secret,
    )
    auth_url, csrf_token = oauth.get_authorization_url('http://localhost:8080')
    webbrowser.open(auth_url)

    auth_code_is_available.wait()
    local_server.stop()
    assert auth_code['state'] == csrf_token
    access_token, refresh_token = oauth.authenticate(auth_code['auth_code'])

    #print('access_token: ' + access_token)
    #print('refresh_token: ' + refresh_token)

    return oauth, access_token, refresh_token
