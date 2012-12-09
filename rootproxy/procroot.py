#!/usr/bin/python
import sys
import subprocess

ptoc_fifo = open(sys.argv[1], "r")
ctop_fifo = open(sys.argv[2], "w")

while True:
  subprocesscommand = eval(ptoc_fifo.readline())
  if subprocesscommand[0] == "end":
    break 
  print subprocesscommand
  if subprocesscommand[0] == "cmd":
    try: 
      result = ("OK", subprocess.check_output(subprocesscommand[1]))
    except subprocess.CalledProcessError as e:
      result = ("FAIL", e.output)
  ctop_fifo.write(repr(result)+"\n")
  ctop_fifo.flush()
  