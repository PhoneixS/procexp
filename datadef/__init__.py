"""data definitions between server and client"""
class ServerPidRequest(object):
  """request to server to do request on given pid"""
  def __init__(self, pid, req, data):
    self.pid = pid
    self.req = req
    self.data = data
  def __repr__(self):
    return "pid:" + repr(self.pid) + " req:"+repr(self.req) + " data:" + repr(self.data)