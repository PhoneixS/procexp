import httplib
import time
conn = httplib.HTTPConnection("www.google.nl")
i = 1
while True:
  conn.request("GET", "/index.html")
  r1 = conn.getresponse()
  v1 = r1.read()
  time.sleep(0.01)
  i += 1

