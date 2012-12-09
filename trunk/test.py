import rootproxy
import os
import uuid
import threading
import time

def readFifo(f):
  theFile = open(f,"r")
  while True:
    print theFile.readline()

fifo = "/tmp/test"+str(uuid.uuid4()) #ParentTOChild
os.mkfifo(fifo)

t = threading.Thread(target=readFifo, args=(fifo, ))
t.daemon = True
t.start()

rootproxy.start()

rootproxy.doContinuousCommand(["tcpdump", "-U" , "-l", "-q", "-nn", "-t", "-i",  "any"], fifo)

print rootproxy.doCommand(["ls", "-al"])

time.sleep(260)
rootproxy.end()