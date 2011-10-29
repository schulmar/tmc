#!/usr/bin/env python
#
# GBX extension of XML-RPC client library. The GBX transport protocol is used
# for communication with Nadeo's Dedicated Server for Trackmania.
#
# Notes:
# This module requires Python version 2.3 or newer.
#
# History:
# 2006-04-19 Marck  First version
# 2006-04-21 Marck  Protocol type "gbx" is case-insensitive.
# 2006-04-27 Marck  Compatibility fix: With dictionaries, use has_key()
#                   instead of 'in'.
#                   __default_address__ configurable through environment
#                   variable GBX_ADDRESS.
# 2006-05-05 Marck  Fix: Methods readCB() and tick() with a timeout of 0 are
#                   actually non-blocking now.
# 2006-05-10 Marck  Use module struct instead of own implementations for
#                   (un)packing binary data.
# 2006-05-12 Marck  Fix: In class Transport, correctly handle data which
#                   has been sent or received only partially over socket
#                   connection.
# 2006-06-28 Marck  Added a timeout for connecting to dedicated server with
#                   connect() in Transport class.
# 2006-07-08 Marck  Fix: Client.remove_method() requires only one argument
#                   instead of two.
# 2006-08-07 Marck  Make socket communication more robust.
# 2006-09-20 Marck  Compatibility fix for Python 2.5.
# 2006-09-21 Marck  Fully compatible with xmlrpclib in Python 2.5.
#
# This work has been created by Marck (marck00@bigfoot.com) and is licensed
# under the Creative Commons Attribution-NonCommercial-ShareAlike 2.0 Germany
# License. To view a copy of this license, visit
# http://creativecommons.org/licenses/by-nc-sa/2.0/de/ or send a letter to
# Creative Commons, 543 Howard Street, 5th Floor, San Francisco, California,
# 94105, USA.
#
# --------------------------------------------------------------------
# The XML-RPC client interface is
#
# Copyright (c) 1999-2002 by Secret Labs AB
# Copyright (c) 1999-2002 by Fredrik Lundh
#
# Confer to module xmlrpclib.py in the Python installation directory for
# more information.

"""Extends module xmlrpclib with support for the "gbx" protocol used by
Trackmania Dedicated Server."""

import xmlrpclib
from xmlrpclib import Fault, Binary, DateTime
import struct

__version__ = '1.3'
__author__ = 'Marck (marck00@bigfoot.com)'
__default_address__ = '127.0.0.1:5000'
__connect_timeout__ = 5.0 # in seconds

#
# Exceptions
#
class ProtocolError(xmlrpclib.ProtocolError):
    """Indicates an GBX protocol error."""
    def __init__(self, url, errcode, errmsg):
        xmlrpclib.ProtocolError.__init__(self, url, errcode, errmsg, '')
        self.url = url
        self.errcode = errcode
        self.errmsg = errmsg

class ConnectionError(ProtocolError):
    """Indicates a problem with the connection."""
    def __init__(self, errcode, errmsg):
        ProtocolError.__init__(self, '', errcode, errmsg)
    def __repr__(self):
        return "<ConnectionError %d: %s>" % (self.errcode, self.errmsg)

#
# Registry
#
class Registry:
    """A registry for XML-RPC callbacks coming from a server.
    This is a simplified implementation based on the method registry in
    xmlrpc-c and xmlrpc_registry.py."""

    def __init__(self):
        self._methods = {}
        self._default_method = None

    def add_method(self, callback_name, method):
        """Add a method to the registry."""
        self._methods[callback_name] = method

    def remove_method(self, callback_name):
        """Remove a method from the registry."""
        del self._methods[callback_name]

    def set_default_method(self, method):
        """Set a default method to handle otherwise unsupported requests."""
        self._default_method = method

    def dispatch(self, callback_name, params):
        """Dispatch an XML-RPC callback. There is no return value. The default
        method is called with the callback's name as first parameter. If there
        is not a default method, then the callback is ignored."""
        # Try to find our method.
        if self._methods.has_key(callback_name):
            method = self._methods[callback_name]
            args = params
        else:
            method = self._default_method
            args = [callback_name] + list(params)
        # Call our method
        if method:
            apply(method, args)

#
# Transport classes
#
class Transport(xmlrpclib.Transport):
    """Handles an XML-RPC transaction to a Trackmania Dedicated Server via the
    "gbx" protocol.	For each request, a connection is created and released
    after the response has been received."""

    handle_mask = 0x80000000L

    def __init__(self, use_datetime=0):
        try:
            # Parameter use_datetime is available since Python 2.5
            xmlrpclib.Transport.__init__(self, use_datetime)
        except AttributeError:
            pass
        self.verbose = None
        self.protocol = None
        self.connection = None

    def _send(self, sock, data):
        data_len = len(data)
        total_sent = 0
        while total_sent < data_len:
            bytes_sent = sock.send(data[total_sent:])
            if bytes_sent == 0:
                raise socket.error, "socket connection broken"
            total_sent += bytes_sent

    def _recv(self, sock, size):
        data = ''
        while size > 0:
            chunk = sock.recv(size)
            chunk_len = len(chunk)
            if chunk_len == 0:
                raise socket.error, "socket connection broken"
            data += chunk
            size -= chunk_len
        return data

    def request(self, host, handler, request_body, verbose=0):
        """Perform a gbx request."""
        if DEBUG: print "[Transport.request]"
        self.verbose = verbose
        self.connect(host, handler, verbose)
        self.send_request(request_body)
        response = self.parse_response()
        self.disconnect()
        return response

    def connect(self, host, handler, verbose=0):
        """Create a socket connection object from a host descriptor."""
        if DEBUG: print "[Transport.connect(%r, %r)]" % (host, handler)
        import socket, select, errno
        address = host.split(':')
        if verbose:
            print "connect:", address
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(__connect_timeout__)
            s.connect((address[0], int(address[1])))
            # get protocol version
            size = struct.unpack('<L', self._recv(s, 4))[0]
            if size > 64:
                raise ProtocolError(host + handler,
                    xmlrpclib.TRANSPORT_ERROR,
                    'transport error - wrong lowlevel protocol header'
                    )
            protocol = s.recv(size)
            s.settimeout(None)
        except socket.timeout, e:
            raise ConnectionError(errno.ETIMEDOUT, e)
        except socket.error, e:
            if isinstance(e, str):
                raise ConnectionError(errno.EIO, e)
            else:
                 raise ConnectionError(e[0], e[1])
        if protocol == "GBXRemote 1":
            self.protocol = 1
        elif protocol == "GBXRemote 2":
            self.protocol = 2
            self.handle = 0x80000000L
        else:
            raise ProtocolError(host + handler,
                xmlrpclib.TRANSPORT_ERROR,
                'transport error - wrong lowlevel protocol header'
                )
        if verbose > 1:
            print "protocol version: GBXRemote", self.protocol
        self.connection = s

    def send_request(self, request_body):
        """Send XML-RPC string."""
        if DEBUG: print "[Transport.send_request]"
        header = struct.pack('<L', len(request_body)) # Size of XML data
        if self.protocol == 2:
            header += struct.pack('<L', self.handle) # Context handle
        if self.verbose > 1:
            text = "snd header: length=%d" % len(request_body)
            if self.protocol == 2:
                text += " handle=0x%X" % self.handle
            print text
        self._send(self.connection, header)
        if self.verbose:
            print "snd body:", repr(request_body)
        self._send(self.connection, request_body)

    def parse_response(self):
        """Receive and parse response and handle any callbacks."""
        if DEBUG: print "[Transport.parse_response]"
        handle = None
        while handle != self.handle:
            handle, response = self._receive()
            self._handle_callback(handle, response)
        if self.verbose:
            print "rcv body:", repr(response)
        return self._parse(response)

    def _receive(self):
        """Receive message from server."""
        header = self._recv(self.connection, 4)
        size = struct.unpack('<L', header)[0] # Size of XML data
        if self.protocol == 1:
            handle = self.__class__.handle_mask
        elif self.protocol == 2:
            # Context handle
            handle = struct.unpack('<L', self._recv(self.connection, 4))[0]
            if self.verbose > 1:
                print "rcv header: handle=0x%X" % handle
        if (handle == 0 or size == 0 or size > 256*1024):
            raise ProtocolError('', xmlrpclib.PARSE_ERROR,
                 'transport error - connection interrupted.')
        data = self._recv(self.connection, size)
        return handle, data

    def _handle_callback(self, handle, msg):
        """Handle callbacks. Return True for an actual callback, otherwise False."""
        return False # ignore callbacks

    def _parse(self, xml_msg):
        """Parse XML data of response."""
        parser, unmarsh = self.getparser()
        parser.feed(xml_msg)
        parser.close()
        return unmarsh.close()

    def disconnect(self):
        if DEBUG: print "[Transport.disconnect]"
        if self.connection:
            self.connection.close()

class TrackmaniaTransport(Transport):
    """Handles a XML-RPC transaction to a Trackmania Dedicated Server.
    Methods can be registered for callback handling."""

    def __init__(self):
        Transport.__init__(self)
        self.registry = Registry()

    def request(self, host, handler, request_body, verbose=0):
        if DEBUG: print "[%s.request]" % self.__class__.__name__
        self.verbose = verbose
        try:
            if not self.connection:
                raise ConnectionError(xmlrpclib.TRANSPORT_ERROR, "Not connected")
        except AttributeError:
            raise ConnectionError(xmlrpclib.TRANSPORT_ERROR, "Not connected")
        self.send_request(request_body)
        return self.parse_response()

    def wait_callback(self, timeout=None, verbose=0):
        """Wait for a callback message. Returns True, if a callback was received."""
        import select
        if not self.connection:
            raise ProtocolError('', xmlrpclib.TRANSPORT_ERROR,
                 'transport error - client not initialized.')
        self.verbose = verbose
        if timeout == None:
            incoming, outgoing, errornous = select.select([self.connection], [], [self.connection])
        else:
            incoming, outgoing, errornous = select.select([self.connection], [], [self.connection], timeout)
        result = False
        if incoming:
            handle, msg = self._receive()
            result = self._handle_callback(handle, msg)
        return result

    def _handle_callback(self, handle, msg):
        """Relay callbacks to registered methods. Return True for an actual
        callback, otherwise False."""
        if handle & self.__class__.handle_mask == 0:
            # this is a callback, not our response!
            if self.verbose:
                print "rcv body:", repr(msg)
            params, name = xmlrpclib.loads(msg)
            self.registry.dispatch(name, params)
            return True
        else:
            return False


class AlternativeTransport(TrackmaniaTransport):
    """Handles an XML-RPC transaction to a Trackmania Dedicated Server.
    Callbacks are collected in a list."""

    def __init__(self):
        TrackmaniaTransport.__init__(self)
        self.registry = None # no registry used here
        self.callbacks = []  # maintain a callback list instead

    def get_callbacks(self):
        """Return the list of collected callback messages and start a new list"""
        result = self.callbacks
        self.callbacks = []
        return result

    def wait_callback(self, timeout=None, verbose=0):
        """Wait for a callback message. Returns True, if a callback was received."""
        if self.callbacks:
            return True
        return TrackmaniaTransport.wait_callback(self, timeout, verbose)

    def _handle_callback(self, handle, msg):
        """Collect callbacks. Return True for an actual callback, otherwise False."""
        if handle & self.__class__.handle_mask == 0:
            # this is a callback, not our response!
            # just add it to the message list for the user to read.
            if self.verbose:
                print "rcv body:", repr(msg)
            params, name = xmlrpclib.loads(msg)
            self.callbacks.append([name] + list(params))
            return True
        else:
            return False

#
# Server proxies
#
class Proxy(xmlrpclib.ServerProxy):
    """Adds "gbx" protocol to class ServerProxy of module xmlrpclib."""

    def __init__(self, uri, transport=None, encoding=None, verbose=0,
                 allow_none=0, use_datetime=0):
        # establish a "logical" server connection
        if DEBUG: print "[Proxy.__init__(%s, %s, %s, %s, %s, %s)]" % \
            (uri, transport, encoding, verbose, allow_none, use_datetime)
        # get the url
        import urllib
        type, host = urllib.splittype(uri)
        if type.lower() != "gbx":
            try:
                # Parameter use_datetime is available since Python 2.5
                xmlrpclib.ServerProxy.__init__(self, uri, transport, encoding,
                    verbose, allow_none, use_datetime)
            except TypeError:
                xmlrpclib.ServerProxy.__init__(self, uri, transport, encoding,
                    verbose, allow_none)
        else:
            self._ServerProxy__host, self._ServerProxy__handler = urllib.splithost(host)
            if not self._ServerProxy__handler:
                self._ServerProxy__handler = "/RPC2"

            self._ServerProxy__transport = transport or Transport(use_datetime)
            self._ServerProxy__encoding = encoding
            self._ServerProxy__verbose = verbose
        if DEBUG: print type, self._ServerProxy__host, \
            self._ServerProxy__handler, self._ServerProxy__transport, \
            self._ServerProxy__encoding, self._ServerProxy__verbose

class _BaseClient(Proxy):
    """Base class for access to an XML-RPC server with "gbx" protocol.
    Analogously to the PHP and C implementations, this class requires explicit
    initialization and release of a connection."""

    def __init__(self, address, transport, verbose):
        if DEBUG: print "[%s.__init__]" % self.__class__.__name__
        Proxy.__init__(self, "gbx://"+address, transport, None, verbose)
        if DEBUG: print self._ServerProxy__host, self._ServerProxy__handler, self._ServerProxy__transport, self._ServerProxy__encoding, self._ServerProxy__verbose

    def init(self):
        """Connect to server."""
        if DEBUG: print "[%s.init]" % self.__class__.__name__
        self._ServerProxy__transport.connect(
            self._ServerProxy__host,
            self._ServerProxy__handler,
            self._ServerProxy__verbose)

    def release(self):
        """Disconnect from server."""
        if DEBUG: print "[%s.release]" % self.__class__.__name__
        if self._ServerProxy__transport:
            self._ServerProxy__transport.disconnect()

class AlternativeClient(_BaseClient):
    """Access an XML-RPC server with "gbx" protocol.
    Callbacks are collected in a list."""

    def __init__(self, address=__default_address__, verbose=0):
        _BaseClient.__init__(self, address, AlternativeTransport(), verbose)

    def release(self):
        """Disconnect from server."""
        _BaseClient.release(self)
        self.getCBResponses() # empty the callback list

    def readCB(self, timeout=None):
        """Receive a callback. Waits a limited time for the arrival of a callback,
        if a timeout is specified as a floating point number in seconds. A timeout
        of 0 does not wait but just polls. Returns True, if a callback was received."""
        return self._ServerProxy__transport.wait_callback(timeout, self._ServerProxy__verbose)

    def getCBResponses(self):
        """Return a list of callbacks received since last call or program start."""
        return self._ServerProxy__transport.get_callbacks()


class Client(_BaseClient):
    """Access an XML-RPC server with "gbx" protocol.
    Callback handling is done by registered methods."""

    def __init__(self, address=__default_address__, verbose=0):
        _BaseClient.__init__(self, address, TrackmaniaTransport(), verbose)

    def add_method(self, callback_name, method):
        """Set handler method for the specified callback in the callback registry."""
        self._ServerProxy__transport.registry.add_method(callback_name, method)

    def remove_method(self, callback_name):
        """Remove handler method for the specified callback from the callback registry."""
        self._ServerProxy__transport.registry.remove_method(callback_name)

    def set_default_method (self, method):
        """Set a default method to handle otherwise unsupported callbacks."""
        self._ServerProxy__transport.registry.set_default_method(method)

    def tick(self, timeout=None):
        """Wait for and process any callbacks for at most the specified period of time.
        The timeout value is specified as a floating point number in seconds.
        The method is non-blocking when timeout is 0. Without any timeout specified,
        wait forever."""
        self._ServerProxy__transport.wait_callback(timeout, self._ServerProxy__verbose)

#
# Test procedures
#
def ListMethods(server):
    print "Available methods:"
    # Query list of methods
    methods = server.system.listMethods()
    # Retrieve method info
    for method in methods:
        signatures = server.system.methodSignature(method)
        help = server.system.methodHelp(method)
        for signature in signatures:
            args = ", ".join(signature[1:])
            print "%s %s(%s)" % (signature[0], method, args)
        print "\t%s\n" % help

def ListGbxMethods():
    client = Client(__default_address__, 0)
    client.init()
    ListMethods(client)
    client.release()

def log_callback(name, *args):
    def typename(x):
        return type(x).__name__
    import time
    print time.strftime("[%Y-%m-%d %H:%M:%S]"),
    print "%s(%s)," % (name, ', '.join(map(repr, args))),
    print "Signature: [%s]" % ', '.join(map(typename, args))

def ShowCallbacks(duration):
    import time
    print "*** Using registered callback handler for %d seconds" % duration
    client = Client(__default_address__, 0)
    client.add_method('TrackMania.PlayerCheckpoint', None) # ignore this callback
    client.set_default_method(log_callback)
    client.init()
    try:
        client.EnableCallbacks(True)
        start = time.time()
        while time.time()-start <= duration:
            client.tick(duration)
    finally:
        client.EnableCallbacks(False)
        client.release()

def ShowCallbacksAlternative(duration):
    import time
    print "*** Using alternative callback handling for %d seconds" % duration
    client = AlternativeClient(__default_address__, 0)
    client.init()
    try:
        client.EnableCallbacks(True)
        start = time.time()
        while time.time()-start <= duration:
            client.readCB(duration)
            for callback in client.getCBResponses():
                apply(log_callback, callback)
    finally:
        client.EnableCallbacks(False)
        client.release()

def Test():
    #ListGbxMethods()
    switchtime = 15
    print
    print "*** Logging callbacks, terminate with CTRL-C."
    try:
        while True:
            ShowCallbacks(switchtime)
            ShowCallbacksAlternative(switchtime)
    except KeyboardInterrupt:
        pass

#
# Main
#
import os
__default_address__ = os.environ.get('GBX_ADDRESS', __default_address__)

DEBUG = os.environ.has_key('DEBUG') # Enable debugging output, if environment variable DEBUG is defined

if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        ListMethods(Proxy(sys.argv[1]))
    else:
        Test()
