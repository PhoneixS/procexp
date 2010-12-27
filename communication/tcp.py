'''
TCP
---

Contains primitives for TCP communication. One only needs to create a connection
object, which has an interface that supports sending any Python object. To
create a connection in a client program, use the following code::

  connection = Client((host, port))

The server program can create a server as follows::

  server = Server((host, port))
  connection = server.accept()

Once a connection exists, it can be used by using its
:meth:`send <_Connection.send>` and :meth:`receive <_Connection.receive>`
methods::

  connection.send(some_object)
  some_object = connection.receive()

*accept*, *send* and *receive* block until a new connection is created, the
object is sent and an object is received respectively. In any other case an
exception is raised. All three methods can be unblocked by calling the *close*
method of the :class:`Server` or :class:`_Connection`.

'''

import sys
import socket
import select
import cPickle
import struct

dolog = False


class Const(object):
  '''Base class for const value classes.
     The const value classes are used to group a set of const values. This base class provides
     a constructor, overwrite protection and inversed lookup.'''

  class ConstError(TypeError):
    '''This error is raised when someone tries to rebind a const to a new value.'''
    pass

  def __init__(self):
    '''Const constructor'''
    pass

  def __setattr__(self, name, value):
    '''Override of object.__setattr__.
       This override prevents rebinding a const name to a new value.'''
    if name in self.__dict__:
      raise self.ConstError, 'Cannot rebind const(%s)' % name
    self.__dict__[name] = value

  @classmethod
  def iteritems(cls):
    '''Iterator over the (key, value) items in Const object.'''
    for item in cls.__dict__.iteritems():
      if not str(item[0]).startswith('__'):
        yield item

  @classmethod
  def name(cls, lookup):
    '''Return the string representation of the given constant value.'''
    for key, value in cls.__dict__.iteritems():
      if lookup == value and not str(key).startswith('__'):
        return key
    raise KeyError(lookup)




def log_print(*data):
  global dolog
  if dolog == True:
    for element in data:
      print element,
    print
    
    
class PyPSError(Exception):
  def __init__(self, value):
    self.value = value
  def __str__(self):
    return repr(self.value)

class Platform(Const):
  '''Platform '''
  WINDOWS = 0==sys.platform.find('win')
  LINUX = 0==sys.platform.find('linux')

# Detect support for the MSG_WAITALL flag. A receive with MSG_WAITALL
# returns when all requested data is received. Without this flag, receive
# can return when not all data is received, depending on packet size and loads.
if Platform.WINDOWS:
  # On windows, MSG_WAITALL is supported for NT based versions >= Windows 2003, i.e
  # platform = 2 meaning NT
  # version >= 5.2 meaning Windows 2003
  MSG_WAITALL_SUPPORTED = sys.getwindowsversion()[3] == 2 and \
                          sys.getwindowsversion()[0] * 10 + sys.getwindowsversion()[1] >= 52
  # See WinSock2.h for value of MSG_WAITALL
  MSG_WAITALL = 0x8
elif Platform.LINUX:
  MSG_WAITALL_SUPPORTED = True
  MSG_WAITALL = socket.MSG_WAITALL # @UndefinedVariable pylint: disable-msg=E1101
else:
  raise PyPSError("Unsupported platform.")

class NoData(PyPSError):
  '''Raised when no data is available for a receive with timeout.
  '''
  def __init__(self):
    PyPSError.__init__(self, "No data")

class TCPError(PyPSError):
  '''Raised when;
  -connection is closed when sending, receiving or accepting
  -invalid data is received
  -connection is denied
  '''
  def __init__(self, _id):
    exc = sys.exc_info()[1]
    PyPSError.__init__(self, 'TCP Error: %s, %s' % (_id, exc if exc else 'TCP Error'))

class Connection():
  '''A TCP Connection.'''
  def __init__(self, s, side):
    '''Not to be used. Instantiate a Client or call Server::accept to create a Connection.'''
    self._socket = s
    self._side = side
    log_print("TCP::Connection: %s" % (self, ))

  def __str__(self):
    '''Returns a string identifying the Connection'''
    s = "side: " + self._side
    s += ", self: "
    try:
      s += str(self._socket.getsockname())
    except:
      s += "unknown"
    s += ", peer: "
    try:
      s += str(self._socket.getpeername())
    except:
      s += "unknown"
    return s

  def send(self, _object):
    '''Send object to peer. Raises TCPError when connection is closed or when
    pickling _object fails. Note that both this end and peer can close connection.
    '''
    log_flood = True
    try:
      while not select.select([], [self._socket], [], 0.1)[1]:
        if log_flood:
          log_flood = False
          log_print("TCP Flooding detected for: %s" % (self, ),
                          "TCP Flooding detected")
      payload = cPickle.dumps(_object, cPickle.HIGHEST_PROTOCOL)
      self._socket.sendall(struct.pack(">Q", len(payload)) + payload)
    except:
      raise TCPError(self)

  def sendBuffer(self, _buffer):
    '''Send buffer to peer. Raises TCPError when connection is closed. Note
    that both this end and peer can close connection.
    '''
    log_flood = True
    try:
      while not select.select([], [self._socket], [], 0.1)[1]:
        if log_flood:
          log_flood = False
          log_print("TCP Flooding detected for: %s" % (self, ),
                          "TCP Flooding detected")
      self._socket.sendall(_buffer)
    except:
      raise TCPError(self)

  def _waitForData(self, timeout = None):
    '''If optional argument 'timeout' is None (the default), block if necessary until
    data is available. Raises TCPError when connection is closed.
    If 'timeout' is a positive number, it blocks at most 'timeout' seconds and
    raises the NoData exception if no data was available within that time.
    '''
    if None is timeout or timeout < 0:
      # Block until data becomes available.
      try:
        while not select.select([self._socket], [], [], 0.1)[0]:
          pass
      except:
        raise TCPError(self)
    else:
      # Wait at most timeout seconds for data to become available.
      try:
        s = select.select([self._socket], [], [], timeout)[0]
      except:
        raise TCPError(self)
      if not s:
        raise NoData

  def _receive(self, length):
    '''Receive length bytes from peer. Raises TCPError when connection is closed.'''
    if MSG_WAITALL_SUPPORTED:
      return self._socket.recv(length, MSG_WAITALL)
    else:
      buffer_ = ""
      while len(buffer_) < length:
        portion = self._socket.recv(length - len(buffer_))
        if len(portion) == 0:
          raise TCPError(self)
        buffer_ += portion
      return buffer_

  def receive(self, timeout = None):
    '''Receive object from peer. Raises TCPError when connection is closed or
    when invalid data is received. Note that both this end and peer can close connection.
    For optional argument timeout see _waitForData method.
    '''
    self._waitForData(timeout)
    try:
      payload_length = struct.unpack(">Q", self._receive(8))[0] 
      return cPickle.loads(self._receive(payload_length))
    except:
      raise TCPError(self)

  def receiveBuffer(self, length, timeout=None, waitall=True):
    '''Receive buffer with expected length from peer.
    Raises TCPError when connection is closed. Note that both this end and peer
    can close connection.
    For optional argument timeout see _waitForData method.
    '''
    self._waitForData(timeout)
    try:
      if waitall:
        buffer_ = self._receive(length)
      else:
        buffer_ = self._socket.recv(length)
    except:
      raise TCPError(self)
    if (not buffer_) or (waitall and (len(buffer_) != length)):
      raise TCPError(self)
    return buffer_

  def receiveLine(self, timeout = None):
    '''Receive one entire line from peer. A trailing newline character is kept in
    the string.
    Raises TCPError when connection is closed. Note that both this end and peer
    can close connection.
    For optional argument timeout see _waitForData method.
    Note that this performs bad, 100 times slower then receive.
    '''
    self._waitForData(timeout)
    line = ""
    while True:
      try:
        c = self._receive(1)
      except:
        raise TCPError(self)
      if len(c) == 0:
        raise TCPError(self)
      line += c
      if line[-1] == '\n':
        break
    return line

  def close(self):
    '''Close the Connection and notify the peer that we stop.'''
    try:
      self._socket.shutdown(socket.SHUT_RDWR)
    except:
      # Note that shutdown may fail when other side is down
      pass
    self._socket.close()


class Server(object):
  '''A TCP server.'''
  def __init__(self, address):
    try:
      self.__server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      self.__server_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
      self.__server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
      self.__server_socket.bind(address)
      self.__server_socket.listen(5)
    except:
      raise TCPError(address)
    log_print("TCP::Server: %s" % (self, ))

  def __str__(self):
    '''Returns a string identifying the Server'''
    s = "self: "
    try:
      s += str(self.__server_socket.getsockname())
    except:
      s += "unknown"
    return s

  def accept(self):
    '''Returns a Connection. Raises exception when server is closed.'''
    try:
      while not select.select([self.__server_socket], [], [], 0.1)[0]:
        pass
      return Connection(self.__server_socket.accept()[0], 'server')
    except:
      raise TCPError(self)

  def close(self):
    '''Close the Server.'''
    self.__server_socket.close()


class Client(Connection):
  '''A TCP client'''
  def __init__(self, address):
    try:
      client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      client_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
      # Note that server side can close this connection after connect returns
      # when maximum number of queued connections is exceeded. Also note that
      # in that case accept on the server side does not return. Also note that
      # socket peer host name is "0.0.0.0" in that case.
      client_socket.connect(address)
      Connection.__init__(self, client_socket, 'client')
    except:
      raise TCPError(address)

def get_fqdn():
  """get fully qualified domain name """
  return socket.getfqdn()
