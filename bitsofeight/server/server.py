__author__ = 'arnavkhare'

import re
import os

from ws4py import configure_logger
configure_logger()

from wsgiref.simple_server import make_server
from ws4py.websocket import WebSocket
from ws4py.server.wsgirefserver import WSGIServer, WebSocketWSGIRequestHandler
from ws4py.server.wsgiutils import WebSocketWSGIApplication

TEMPLATE_ROOT = os.path.dirname(os.path.abspath(__file__))


def not_found(environ, start_response):
    """Called if no URL matches."""
    start_response('404 NOT FOUND', [('Content-Type', 'text/plain')])
    return ['Not Found']


def render_from_template(template):
    return open(os.path.join(TEMPLATE_ROOT, template)).read()


def application(environ, start_response):
    """
    The main WSGI application. Dispatch the current request to
    the functions from above and store the regular expression
    captures in the WSGI environment as  `myapp.url_args` so that
    the functions from above can access the url placeholders.

    If nothing matches call the `not_found` function.
    """
    path = environ.get('PATH_INFO', '').lstrip('/')
    for regex, callback in urls:
        match = re.search(regex, path)
        if match is not None:
            # environ['myapp.url_args'] = match.groups()
            return callback(environ, start_response)
    return not_found(environ, start_response)


def index(environ, start_response):
    """Server the main HTML page"""
    # get the name from the url if it was specified there.
    start_response('200 OK', [('Content-Type', 'text/html')])
    return [render_from_template('index.html')]


class EchoWebSocket(WebSocket):
    def received_message(self, message):
        """
        Automatically sends back the provided ``message`` to
        its originating endpoint.
        """
        self.send(message.data, message.is_binary)

websocket_application = WebSocketWSGIApplication(handler_cls=EchoWebSocket)

# map urls to functions
urls = [
    (r'^$', index),
    (r'^ws$', websocket_application),
]


server = make_server('127.0.0.1', 9000, server_class=WSGIServer,
                     handler_class=WebSocketWSGIRequestHandler,
                     app=application)
server.initialize_websockets_manager()
server.serve_forever()
