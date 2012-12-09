import subprocess
import os
import uuid

ptoc = "/tmp/ptoc"+str(uuid.uuid4()) #ParentTOChild
ctop = "/tmp/ctop"+str(uuid.uuid4()) #ChildTOParent

os.mkfifo(ptoc) #ParentToChild
os.mkfifo(ctop) #ChildTOParent

p = subprocess.Popen(["pkexec", os.path.realpath(__file__).replace(__file__, "procroot.py"), ptoc, ctop])

#p = subprocess.Popen(["./procroot.py", ptoc, ctop])

ptoc_file = open(ptoc, "w")
ctop_file = open(ctop, "r")

ptoc_file.write(repr(("cmd", ['ls','-al']))+"\n")
ptoc_file.flush()  
data = ctop_file.readline()
ptoc_file.write(repr(("end",))+"\n")
