__author__ = 'arnavkhare'

import re
import os

from Queue import Queue
from ws4py import configure_logger
configure_logger()

from wsgiref.simple_server import make_server
from ws4py.websocket import WebSocket
from ws4py.server.wsgirefserver import WSGIServer, WebSocketWSGIRequestHandler
from ws4py.server.wsgiutils import WebSocketWSGIApplication

from ..orders import OrderProcessor


TEMPLATE_ROOT = os.path.dirname(os.path.abspath(__file__))

orders_queue = None
order_processor = OrderProcessor()


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


import os.path
from mimetypes import guess_type

BASE = ['assets', 'web']


def serve(environ, start_response):
    """Server the main HTML page"""
    path = environ.get('PATH_INFO', '')
    file_parts = re.sub('^/assets/', '', path).split('/')
    local_path = os.path.join(*(BASE + file_parts))
    try:
        contents = open(local_path, 'r').read()
    except (IOError, OSError):
        start_response('404 Not Found', [('Content-Type', 'text/html')])
        return ['<h1>File not found</h1>']

    type, encoding = guess_type(path)
    type = type or 'application/octet-stream'
    if encoding:
        type += '; charset=' + encoding
    start_response('200 OK', [('Content-Type', type)])
    return [contents]


class EchoWebSocket(WebSocket):
    def received_message(self, message):
        """
        Automatically sends back the provided ``message`` to
        its originating endpoint.
        """
        self.send(message.data, message.is_binary)


socket = None

import json


class GameWebSocket(WebSocket):
    def opened(self):
        global socket
        socket = self
        system_queue.put('connected')

    def received_message(self, message):
        global orders_queue
        command = message.data
        self.process_command(command)

        response = "Command sent: %s" % command
        self.send(response, False)

    def closed(self, *args):
        global socket
        socket = None
        print "Lost connection to client."
        system_queue.put('disconnected')

    def process_command(self, command):
        cmd = getattr(order_processor, command, None)
        if cmd:
            order = cmd()
            orders_queue.put(order)


websocket_application = WebSocketWSGIApplication(handler_cls=GameWebSocket)

# map urls to functions
urls = [
    (r'^$', index),
    (r'^assets/(.*)$', serve),
    (r'^ws$', websocket_application),
]


def serve(host, port, orders_q, system_q):
    global orders_queue, system_queue
    orders_queue = orders_q
    system_queue = system_q

    # start server
    server = make_server(host, port, server_class=WSGIServer,
                         handler_class=WebSocketWSGIRequestHandler,
                         app=application)
    server.initialize_websockets_manager()
    server.serve_forever()


def send_msg(msg):
    if socket:
        socket.send(json.dumps(msg))


if __name__ == '__main__':
    import Queue
    serve('127.0.0.1', 9000, Queue.Queue())
