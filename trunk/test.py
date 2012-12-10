import rootproxy
import os
import uuid
import threading

def readFifo(f):
  theFile = open(f,"r")
  while True:
    print theFile.readline(),

fifo = "/tmp/test"+str(uuid.uuid4()) #ParentTOChild
os.mkfifo(fifo)

t = threading.Thread(target=readFifo, args=(fifo, ))
t.daemon = True
t.start()

rootproxy.start()

rootproxy.doContinuousCommand(["tcpdump", "-U" , "-l", "-q", "-nn", "-t", "-i",  "any"], fifo)

for _ in xrange(300):
  rootproxy.doCommand(["sleep", "1"])
rootproxy.end()